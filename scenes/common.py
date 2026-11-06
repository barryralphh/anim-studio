import bpy, math, random, sys, os


def parse_args():
    d = {'shard': 0, 'shards': 1, 'out': 'out', 'frames': 240, 'preview': 0}
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for i in range(0, len(a) - 1, 2):
        k = a[i].lstrip('-')
        if k in d:
            d[k] = type(d[k])(a[i + 1])
    return d


# ---------------- colour / math helpers (pure python) ----------------
def lin1(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lin(rgb): return tuple(lin1(c) for c in rgb)
def hexc(h):
    h = h.lstrip('#')
    return lin(tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)))


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def lerp(a, b, u): return a + (b - a) * u
def mixc(c1, c2, u): return tuple(lerp(c1[i], c2[i], u) for i in range(3))
def shade(c, k): return tuple(clamp(x * k, 0, 1) for x in c)
def ease(u):
    u = clamp(u)
    return u * u * (3 - 2 * u)


def smooth(a, b, x):
    return ease((x - a) / (b - a))


def vnorm(v):
    l = math.sqrt(sum(c * c for c in v))
    return tuple(c / l for c in v)


def haze(col, dist, hcol, k=0.003):
    return mixc(col, hcol, 1 - math.exp(-dist * k))


def look_euler(d):
    dx, dy, dz = d
    e = math.atan2(dz, math.hypot(dx, dy))
    return (math.pi / 2 + e, 0.0, math.atan2(-dx, dy))


# ---------------- transforms ----------------
ID = lambda p: p
def T(x, y, z): return lambda p: (p[0] + x, p[1] + y, p[2] + z)
def S(x, y, z): return lambda p: (p[0] * x, p[1] * y, p[2] * z)
def RX(a):
    c, s = math.cos(a), math.sin(a)
    return lambda p: (p[0], p[1] * c - p[2] * s, p[1] * s + p[2] * c)
def RY(a):
    c, s = math.cos(a), math.sin(a)
    return lambda p: (p[0] * c + p[2] * s, p[1], -p[0] * s + p[2] * c)
def RZ(a):
    c, s = math.cos(a), math.sin(a)
    return lambda p: (p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2])
def chain(*fs):
    def g(p):
        for f in fs:
            p = f(p)
        return p
    return g


# ---------------- mesh builder with per-face colour ----------------
class M:
    def __init__(s):
        s.v, s.f, s.c = [], [], []

    def add(s, verts, faces, col, tf=ID):
        o = len(s.v)
        s.v.extend(tf(p) for p in verts)
        for i, fc in enumerate(faces):
            s.f.append(tuple(o + j for j in fc))
            s.c.append(col[i] if isinstance(col, list) else col)

    def transform(s, tf):
        s.v = [tf(p) for p in s.v]

    def merge(s, o):
        n = len(s.v)
        s.v.extend(o.v)
        s.f.extend(tuple(n + j for j in fc) for fc in o.f)
        s.c.extend(o.c)

    def tri(s, a, b, c, col, tf=ID):
        s.add([a, b, c], [(0, 1, 2)], col, tf)

    def quad(s, a, b, c, d, col, tf=ID):
        s.add([a, b, c, d], [(0, 1, 2, 3)], col, tf)

    def box(s, cx, cy, cz, sx, sy, sz, col, tf=ID, top=(1.0, 1.0)):
        if not isinstance(top, tuple):
            top = (top, top)
        hx, hy = sx / 2, sy / 2
        tx, ty = hx * top[0], hy * top[1]
        v = [(-hx, -hy, 0), (hx, -hy, 0), (hx, hy, 0), (-hx, hy, 0),
             (-tx, -ty, sz), (tx, -ty, sz), (tx, ty, sz), (-tx, ty, sz)]
        v = [(x + cx, y + cy, z + cz) for x, y, z in v]
        f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        s.add(v, f, col, tf)

    def cyl(s, cx, cy, cz, r, h, n, col, tf=ID, r2=None, cap=True):
        r2 = r if r2 is None else r2
        v = [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n), cz) for i in range(n)]
        f = []
        if r2 <= 1e-6:
            v.append((cx, cy, cz + h))
            for i in range(n):
                f.append((i, (i + 1) % n, n))
        else:
            v += [(cx + r2 * math.cos(2 * math.pi * i / n), cy + r2 * math.sin(2 * math.pi * i / n), cz + h) for i in range(n)]
            for i in range(n):
                j = (i + 1) % n
                f.append((i, j, n + j, n + i))
            if cap:
                f.append(tuple(range(n, 2 * n)))
        if cap:
            f.append(tuple(range(n - 1, -1, -1)))
        s.add(v, f, col, tf)

    def sphere(s, cx, cy, cz, r, col, tf=ID, rings=4, n=8, half=False, sx=1.0, sy=1.0, sz=1.0):
        pm = math.pi / 2 if half else math.pi
        v = [(0.0, 0.0, r * sz)]
        rng = list(range(1, rings + 1)) if half else list(range(1, rings))
        for j in rng:
            ph = pm * j / rings
            for i in range(n):
                th = 2 * math.pi * i / n
                v.append((r * sx * math.sin(ph) * math.cos(th), r * sy * math.sin(ph) * math.sin(th), r * sz * math.cos(ph)))
        f = []
        nr = len(rng)
        for i in range(n):
            f.append((0, 1 + i, 1 + (i + 1) % n))
        for j in range(nr - 1):
            a, b = 1 + j * n, 1 + (j + 1) * n
            for i in range(n):
                k = (i + 1) % n
                f.append((a + i, b + i, b + k, a + k))
        if not half:
            v.append((0.0, 0.0, -r * sz))
            bot = len(v) - 1
            last = 1 + (nr - 1) * n
            for i in range(n):
                f.append((bot, last + (i + 1) % n, last + i))
        s.add([(x + cx, y + cy, z + cz) for x, y, z in v], f, col, tf)

    def to_mesh(s, name):
        me = bpy.data.meshes.new(name)
        me.from_pydata(s.v, [], s.f)
        me.update()
        ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
        flat = []
        for fc, c in zip(s.f, s.c):
            flat += [c[0], c[1], c[2], 1.0] * len(fc)
        ca.data.foreach_set('color', flat)
        return me

    def to_obj(s, name, mat, smooth_shade=False):
        me = s.to_mesh(name)
        if smooth_shade:
            me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        ob.data.materials.append(mat)
        return ob


class Dyn:
    """object whose mesh is rebuilt every frame"""
    def __init__(s, name, mat):
        s.name = name
        s.ob = bpy.data.objects.new(name, M().to_mesh(name))
        bpy.context.scene.collection.objects.link(s.ob)
        s.ob.data.materials.append(mat)
        s.mat = mat

    def set(s, m, smooth_shade=False):
        old = s.ob.data
        me = m.to_mesh(s.name)
        if smooth_shade:
            me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
        me.materials.append(s.mat)
        s.ob.data = me
        bpy.data.meshes.remove(old)


class Cloth:
    """grid of quads whose vertices are driven by pos_fn(u, v, t)"""
    def __init__(s, name, mat, nx, ny, pos_fn, colfn, smooth_shade=True):
        s.nx, s.ny, s.pos_fn = nx, ny, pos_fn
        v = [(0.0, 0.0, 0.0)] * ((nx + 1) * (ny + 1))
        f, c = [], []
        for j in range(ny):
            for i in range(nx):
                a = j * (nx + 1) + i
                f.append((a, a + 1, a + nx + 2, a + nx + 1))
                c.append(colfn(i, j))
        m = M()
        m.v, m.f, m.c = v, f, c
        s.me = m.to_mesh(name)
        if smooth_shade:
            s.me.polygons.foreach_set('use_smooth', [True] * len(s.me.polygons))
        s.ob = bpy.data.objects.new(name, s.me)
        bpy.context.scene.collection.objects.link(s.ob)
        s.ob.data.materials.append(mat)
        s.update(0.0)

    def update(s, t):
        flat = []
        for j in range(s.ny + 1):
            for i in range(s.nx + 1):
                flat.extend(s.pos_fn(i / s.nx, j / s.ny, t))
        s.me.vertices.foreach_set('co', flat)
        s.me.update()


# ---------------- materials ----------------
def vc_material(name='VC', rough=0.85, spec=0.15):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    at = nt.nodes.new('ShaderNodeAttribute')
    at.attribute_name = 'Col'
    nt.links.new(at.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    try:
        b.inputs['Specular IOR Level'].default_value = spec
    except KeyError:
        b.inputs['Specular'].default_value = spec
    return m


def emit_material(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    e = nt.nodes.new('ShaderNodeEmission')
    e.inputs['Color'].default_value = (color[0], color[1], color[2], 1.0)
    e.inputs['Strength'].default_value = strength
    o = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(e.outputs[0], o.inputs[0])
    return m


# ---------------- world / sky ----------------
def sky_world(sun_dir, zenith, horizon, ground, glow, sun_col, glow_pow=5.0, glow_amt=1.0,
              sun_amt=12.0, sun_r=0.014, strength=1.0, hz_pow=1.0, z_scale=1.6):
    w = bpy.data.worlds.new('W')
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)

    def node(t, **kw):
        n = nt.nodes.new(t)
        for k, v in kw.items():
            setattr(n, k, v)
        return n

    def mth(op, a=None, b=None, clamp_=False):
        n = node('ShaderNodeMath', operation=op, use_clamp=clamp_)
        for i, x in enumerate((a, b)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                n.inputs[i].default_value = x
            else:
                nt.links.new(x, n.inputs[i])
        return n.outputs[0]

    def mix(fac, c1, c2, blend='MIX'):
        n = node('ShaderNodeMixRGB', blend_type=blend)
        if isinstance(fac, (int, float)):
            n.inputs[0].default_value = fac
        else:
            nt.links.new(fac, n.inputs[0])
        for i, c in ((1, c1), (2, c2)):
            if isinstance(c, tuple):
                n.inputs[i].default_value = (c[0], c[1], c[2], 1.0)
            else:
                nt.links.new(c, n.inputs[i])
        return n.outputs[0]

    tc = node('ShaderNodeTexCoord')
    vn = node('ShaderNodeVectorMath', operation='NORMALIZE')
    nt.links.new(tc.outputs['Generated'], vn.inputs[0])
    sep = node('ShaderNodeSeparateXYZ')
    nt.links.new(vn.outputs[0], sep.inputs[0])
    z = sep.outputs[2]
    t = mth('MULTIPLY', mth('ADD', z, 0.02), z_scale, True)
    t = mth('POWER', t, hz_pow)
    sky = mix(t, horizon, zenith)
    gk = mth('MULTIPLY', mth('SUBTRACT', 0.0, z), 30.0, True)
    base = mix(gk, sky, ground)
    vd = node('ShaderNodeVectorMath', operation='DOT_PRODUCT')
    nt.links.new(vn.outputs[0], vd.inputs[0])
    vd.inputs[1].default_value = sun_dir
    dot = vd.outputs[1]
    pos = mth('MAXIMUM', dot, 0.0)
    g1 = mth('POWER', pos, glow_pow)
    g2 = mth('POWER', pos, glow_pow * 7.0)
    c_hi, c_lo = math.cos(sun_r), math.cos(sun_r * 2.2)
    disc = mth('MULTIPLY', mth('SUBTRACT', dot, c_lo), 1.0 / (c_hi - c_lo), True)
    col = base
    col = mix(1.0, col, mix(1.0, glow, mth('MULTIPLY', g1, glow_amt), 'MULTIPLY'), 'ADD')
    col = mix(1.0, col, mix(1.0, sun_col, mth('MULTIPLY', g2, glow_amt * 1.5), 'MULTIPLY'), 'ADD')
    col = mix(1.0, col, mix(1.0, sun_col, mth('MULTIPLY', disc, sun_amt), 'MULTIPLY'), 'ADD')
    bg = node('ShaderNodeBackground')
    bg.inputs['Strength'].default_value = strength
    nt.links.new(col, bg.inputs['Color'])
    out = node('ShaderNodeOutputWorld')
    nt.links.new(bg.outputs[0], out.inputs[0])
    bpy.context.scene.world = w
    return w


def make_sun(sun_dir, color, strength, angle=0.03, shadow=True, name='Sun'):
    ld = bpy.data.lights.new(name, 'SUN')
    ld.energy = strength
    ld.color = color
    ld.angle = angle
    ld.use_shadow = shadow
    ob = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.rotation_euler = look_euler(tuple(-c for c in sun_dir))
    return ob


def make_camera(lens=35.0, fstop=4.0):
    cd = bpy.data.cameras.new('Cam')
    cd.lens = lens
    cd.clip_start = 0.1
    cd.clip_end = 8000
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = fstop
    ob = bpy.data.objects.new('Cam', cd)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.scene.camera = ob
    return ob


def aim(cam, pos, target):
    cam.location = pos
    d = (target[0] - pos[0], target[1] - pos[1], target[2] - pos[2])
    cam.rotation_euler = look_euler(d)
    cam.data.dof.focus_distance = max(0.5, math.sqrt(sum(c * c for c in d)))


def setup_render(a, samples=48):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    cy = sc.cycles
    cy.device = 'CPU'
    prev = a['preview']
    cy.samples = 14 if prev else samples
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.03
    cy.use_denoising = True
    try:
        cy.denoiser = 'OPENIMAGEDENOISE'
    except Exception:
        pass
    cy.max_bounces = 5
    cy.diffuse_bounces = 3
    cy.glossy_bounces = 2
    cy.sample_clamp_indirect = 6.0
    sc.render.resolution_x = 640 if prev else 1280
    sc.render.resolution_y = 360 if prev else 720
    sc.render.resolution_percentage = 100
    sc.render.fps = 24
    sc.render.image_settings.file_format = 'JPEG'
    sc.render.image_settings.quality = 95
    try:
        sc.view_settings.view_transform = 'Filmic'
        sc.view_settings.look = 'Medium High Contrast'
    except Exception:
        pass
    return sc


def add_glare(mix_=-0.55, threshold=0.85, size=7):
    try:
        sc = bpy.context.scene
        sc.use_nodes = True
        nt = sc.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        rl = nt.nodes.new('CompositorNodeRLayers')
        gl = nt.nodes.new('CompositorNodeGlare')
        gl.glare_type = 'FOG_GLOW'
        gl.quality = 'MEDIUM'
        gl.threshold = threshold
        gl.size = size
        gl.mix = mix_
        co = nt.nodes.new('CompositorNodeComposite')
        nt.links.new(rl.outputs[0], gl.inputs[0])
        nt.links.new(gl.outputs[0], co.inputs[0])
    except Exception as e:
        print('glare skipped', e)


def frame_list(a):
    total = a['frames']
    if a['preview']:
        fr = [int(total * x) for x in (0.0, 0.3, 0.6, 0.92)]
        return fr[a['shard']::a['shards']]
    return list(range(a['shard'], total, a['shards']))


def render_frames(a, update):
    sc = bpy.context.scene
    os.makedirs(a['out'], exist_ok=True)
    for f in frame_list(a):
        update(f / 24.0)
        sc.cycles.seed = f
        sc.render.filepath = os.path.join(a['out'], 'frame_%04d.jpg' % f)
        bpy.ops.render.render(write_still=True)
        print('rendered', f, flush=True)
