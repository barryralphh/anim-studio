
# ===================== ROOFTOP / HOODED FIGURE (original design) =====================
A = parse_args()
random.seed(11)
sc = setup_render(A, samples=56)

SUN = vnorm((-0.32, 0.88, 0.24))
HZ = hexc('#f3b07c')          # haze / horizon colour
sky_world(SUN, zenith=hexc('#27466f'), horizon=hexc('#f6b27c'), ground=hexc('#d79a6a'),
          glow=hexc('#ff9448'), sun_col=hexc('#fff0cc'), glow_pow=4.0, glow_amt=1.25, sun_amt=14.0,
          strength=1.0, hz_pow=0.8, z_scale=1.5)
make_sun(SUN, (1.0, 0.66, 0.38), 5.2, angle=0.045)
make_sun(vnorm((0.35, -0.8, 0.4)), (0.55, 0.68, 1.0), 0.9, angle=0.3, shadow=False, name='Fill')
add_glare()
cam = make_camera(32.0, 3.6)

matCity = vc_material('City', rough=0.92, spec=0.08)
matFig = vc_material('Fig', rough=0.7, spec=0.2)
matCloth = vc_material('Cloth', rough=0.8, spec=0.1)
matEmber = emit_material('Ember', hexc('#ffb259'), 14.0)

GZ = -42.0
sand = ['#e8cda5', '#d6b48a', '#f0dcb9', '#c8a078', '#e2be96', '#dcc39c', '#efd3a8']
roofc = ['#b85f3c', '#a85034', '#c9703f', '#9f4a30']
domec = ['#3aa9a6', '#2f8f8c', '#d9a441', '#5fb5a0', '#e0b04c']

# ---------- ground (rings fade into haze) ----------
g = M()
radii = [0, 40, 90, 160, 260, 420, 700, 1200, 2200, 5000]
NS = 32
CEN = (0.0, 120.0)
gcol = hexc('#b99468')
ring_v = []
for rr in radii:
    ring_v.append([(CEN[0] + rr * math.cos(2 * math.pi * i / NS), CEN[1] + rr * math.sin(2 * math.pi * i / NS), GZ) for i in range(NS)])
for k in range(len(radii) - 1):
    for i in range(NS):
        j = (i + 1) % NS
        a_, b_ = ring_v[k][i], ring_v[k][j]
        c_, d_ = ring_v[k + 1][j], ring_v[k + 1][i]
        mx = (a_[0] + b_[0] + c_[0] + d_[0]) / 4
        my = (a_[1] + b_[1] + c_[1] + d_[1]) / 4
        col = haze(shade(gcol, random.uniform(0.92, 1.05)), math.hypot(mx, my), HZ, 0.0032)
        g.quad(d_, c_, b_, a_, col)
g.to_obj('Ground', matCity)

# ---------- city ----------
city = M()
for jy in range(0, 26):
    for ix in range(-14, 15):
        if random.random() < 0.10:
            continue
        x = ix * 14 + random.uniform(-2, 2)
        y = 24 + jy * 14 + random.uniform(-2, 2)
        dist = math.hypot(x, y)
        w = random.uniform(7.5, 11.5)
        d = random.uniform(7.5, 11.5)
        hgt = random.uniform(4, 10) * (1 + 0.5 * math.exp(-(x / 90.0) ** 2)) + random.choice([0, 0, 3, 6])
        col = haze(hexc(random.choice(sand)), dist, HZ)
        city.box(x, y, GZ, w, d, hgt, col)
        r = random.random()
        z0 = GZ + hgt
        if r < 0.22:
            city.sphere(x, y, z0, min(w, d) * 0.40, haze(hexc(random.choice(domec)), dist, HZ), half=True, rings=3, n=10, sz=0.9)
        elif r < 0.5:
            city.box(x, y, z0, w + 0.5, d + 0.5, 0.6, haze(hexc('#f2dcb8'), dist, HZ))
            city.box(x + random.uniform(-2, 2), y + random.uniform(-2, 2), z0 + 0.6, 2.0, 2.0, 1.4, col)
        elif r < 0.72:
            city.box(x, y, z0, w + 0.8, d + 0.8, 2.4, haze(hexc(random.choice(roofc)), dist, HZ), top=(0.0, 1.0))
        else:
            city.box(x, y, z0, w + 0.4, d + 0.4, 0.5, haze(hexc('#e6caa0'), dist, HZ))
        if random.random() < 0.25:
            h2 = random.uniform(2.5, 5)
            city.box(x + random.uniform(-1.5, 1.5), y + random.uniform(-1.5, 1.5), z0, w * 0.55, d * 0.55, h2, haze(hexc(random.choice(sand)), dist, HZ))
            city.box(x, y, z0 + h2, w * 0.6, d * 0.6, 0.5, haze(hexc('#f2dcb8'), dist, HZ))


def minaret(x, y, h, dist_col=True):
    d = math.hypot(x, y)
    cw = haze(hexc('#efe0c4'), d, HZ)
    cc = haze(hexc(random.choice(domec)), d, HZ)
    city.cyl(x, y, GZ, 1.3, h, 8, cw, r2=0.95)
    city.cyl(x, y, GZ + h * 0.72, 2.0, 0.7, 8, cw)
    city.cyl(x, y, GZ + h * 0.72 + 0.7, 1.1, 0.3, 8, cc)
    city.cyl(x, y, GZ + h, 1.5, 4.5, 8, cc, r2=0.0)
    city.cyl(x, y, GZ + h + 4.5, 0.12, 2.2, 4, cw, r2=0.05)


for k in range(14):
    minaret(random.uniform(-170, 170), random.uniform(70, 320), random.uniform(24, 40))

# grand landmark
LX, LY = 38.0, 92.0
ld_ = math.hypot(LX, LY)
body = haze(hexc('#f0e2c6'), ld_, HZ)
city.box(LX, LY, GZ, 30, 30, 16, body)
city.box(LX, LY, GZ + 16, 31, 31, 1.0, haze(hexc('#d9bd94'), ld_, HZ))
city.sphere(LX, LY, GZ + 17, 12.5, haze(hexc('#2fa3a0'), ld_, HZ), half=True, rings=5, n=14, sz=0.95)
city.cyl(LX, LY, GZ + 17 + 12.5 * 0.95, 0.5, 4.0, 6, haze(hexc('#e8b94a'), ld_, HZ), r2=0.1)
for sx_ in (-1, 1):
    for sy_ in (-1, 1):
        minaret(LX + sx_ * 17, LY + sy_ * 17, 38)
        city.sphere(LX + sx_ * 9, LY + sy_ * 9, GZ + 17, 4.5, haze(hexc('#d9a441'), ld_, HZ), half=True, rings=3, n=8)
city.box(LX, LY - 18, GZ, 20, 8, 9, body)

# citadel
CX_, CY_ = -70.0, 170.0
cd_ = math.hypot(CX_, CY_)
wallc = haze(hexc('#d8b98c'), cd_, HZ)
city.box(CX_, CY_, GZ, 42, 42, 12, wallc)
for k in range(10):
    city.box(CX_ - 21 + k * 4.6, CY_ - 21, GZ + 12, 2.4, 2.4, 2.0, wallc)
for sx_ in (-1, 1):
    for sy_ in (-1, 1):
        city.cyl(CX_ + sx_ * 21, CY_ + sy_ * 21, GZ, 5.5, 22, 8, wallc)
        city.cyl(CX_ + sx_ * 21, CY_ + sy_ * 21, GZ + 22, 6.2, 5.5, 8, haze(hexc('#b85f3c'), cd_, HZ), r2=0.0)
city.to_obj('City', matCity)

# ---------- distant mountains ----------
mt = M()
for k in range(24):
    th = math.radians(random.uniform(-105, 105))
    D = random.uniform(780, 1500)
    px, py = D * math.sin(th), D * math.cos(th)
    rad = random.uniform(130, 240)
    hh = random.uniform(95, 210)
    base_c = haze(hexc(random.choice(['#a68a86', '#9b7f80', '#b49484'])), D, mixc(HZ, hexc('#c9a1b0'), 0.4), 0.0016)
    snow_c = haze(hexc('#fff4ea'), D, HZ, 0.0016)
    mt.cyl(px, py, GZ - 10, rad, hh, 7, base_c, r2=0.0, tf=RZ(random.uniform(0, 1)))
    f_ = 0.70
    mt.cyl(px, py, GZ - 10 + hh * f_, rad * (1 - f_) * 1.02, hh * (1 - f_) * 1.0, 7, snow_c, r2=0.0, tf=RZ(0))
mt.to_obj('Mountains', matCity)

# ---------- foreground tower ----------
tw = M()
stone, stone2, wood = hexc('#d9bd94'), hexc('#c2a173'), hexc('#6b4a2f')
tw.box(0, 0, -60, 8, 8, 60, stone)
tw.box(0, 0, 0, 8.6, 8.6, 0.35, stone2)
tw.box(-4.1, 0, 0.35, 0.5, 8.6, 0.9, stone)
tw.box(4.1, 0, 0.35, 0.5, 8.6, 0.9, stone)
tw.box(0, -4.1, 0.35, 8.6, 0.5, 0.9, stone)
for sx_ in (-1, 1):
    for sy_ in (-1, 1):
        tw.box(sx_ * 4.1, sy_ * 4.1, 0.35, 0.8, 0.8, 2.3, stone2)
        tw.cyl(sx_ * 4.1, sy_ * 4.1, 2.65, 0.75, 0.9, 4, hexc('#b85f3c'), r2=0.0, tf=RZ(math.pi / 4))
tw.box(0, 5.2, 0.05, 0.55, 5.8, 0.3, wood)
tw.box(0, 8.0, 0.02, 0.62, 0.3, 0.36, hexc('#4a3220'))
for yy in (3.2, 5.0, 6.8):
    tw.box(0, yy, 0.0, 0.8, 0.12, 0.38, hexc('#3d2918'))
tw.box(-0.9, 2.0, 0.35, 0.5, 0.5, 0.4, hexc('#8a6a44'))
tw.box(1.0, 1.4, 0.35, 0.6, 0.6, 0.55, hexc('#7a5a38'))
tw.to_obj('Tower', matFig)

# poles + flags
for px_, col_a in ((-3.7, '#c1272d'), (3.7, '#c1272d')):
    pm = M()
    pm.cyl(px_, -3.6, 0.35, 0.07, 5.6, 6, hexc('#3d2918'))
    pm.sphere(px_, -3.6, 5.95, 0.14, hexc('#e8b94a'), rings=2, n=6)
    pm.to_obj('Pole', matFig)

FP = (0.0, 6.9, 0.35)       # figure feet position


def flag_pos(px_, sgn):
    def f(u, v, t):
        x = px_ + sgn * (0.1 + 1.9 * u)
        w = u
        z = 5.85 - 1.0 * v
        y = -3.6 + 0.35 * w * math.sin(5 * u - 6.0 * t + 1.7 * v) + 0.1 * w
        z += 0.12 * w * math.sin(4 * u - 5.0 * t)
        return (x, y, z)
    return f


def flag_col(i, j):
    return hexc('#e8b94a') if j in (3, 4) and False else (hexc('#c1272d') if j != 3 else hexc('#e8b94a'))


flags = [Cloth('FlagL', matCloth, 10, 6, flag_pos(-3.7, -1), flag_col),
         Cloth('FlagR', matCloth, 10, 6, flag_pos(3.7, 1), flag_col)]

# ---------- the figure (original hooded character) ----------
cream, cream2, leather = hexc('#ece3cf'), hexc('#d7cbb0'), hexc('#4a2f22')
pants, red, skin, shadow_ = hexc('#5a4636'), hexc('#b81f2a'), hexc('#c58f6a'), hexc('#150c0a')
fg = M()
for sx_ in (-0.12, 0.12):
    fg.box(sx_, 0.0, 0.1, 0.17, 0.2, 0.86, pants, top=(0.85, 0.85))
    fg.box(sx_, 0.03, 0.0, 0.2, 0.32, 0.3, leather)
fg.box(0, 0, 0.55, 0.52, 0.34, 0.48, cream2, top=(0.9, 0.9))
fg.box(0, 0, 0.93, 0.5, 0.3, 0.64, cream, top=(1.12, 1.0))
fg.box(0, 0, 0.9, 0.54, 0.34, 0.1, leather)
fg.box(0, 0, 0.86, 0.55, 0.35, 0.06, red)
fg.box(0.0, 0.1, 1.2, 0.5, 0.12, 0.34, leather, tf=RY(0.0))
fg.box(0.0, 0.0, 1.5, 0.62, 0.34, 0.12, leather)
fg.box(0.09, 0.19, 0.48, 0.1, 0.03, 0.42, red)
for sx_ in (-1, 1):
    fg.box(sx_ * 0.34, 0.02, 0.9, 0.13, 0.15, 0.62, cream, top=(0.85, 0.85))
    fg.box(sx_ * 0.34, 0.02, 0.84, 0.15, 0.17, 0.22, leather)
    fg.sphere(sx_ * 0.34, 0.02, 0.8, 0.07, skin, rings=2, n=6)
    fg.box(sx_ * 0.3, 0.0, 1.46, 0.22, 0.28, 0.1, leather)
fg.cyl(0, 0, 1.52, 0.2, 0.26, 8, cream, r2=0.16)
fg.box(0, 0.13, 1.6, 0.2, 0.12, 0.2, shadow_)
fg.cyl(0, 0, 1.74, 0.2, 0.34, 8, cream, r2=0.0, tf=chain(T(0, 0, -1.74), RX(-0.5), T(0, 0.02, 1.74)))
fg.box(0, 0.19, 1.62, 0.1, 0.08, 0.06, skin)
fg.transform(T(*FP))
fg.to_obj('Figure', matFig)


def cloak_pos(u, v, t):
    x = (u - 0.5) * (0.46 + 0.38 * v)
    yb = -0.17 - 0.1 * v - 0.05 * math.sin(math.pi * u) * v
    zb = 1.52 - 1.28 * v
    w = v ** 1.4
    s_ = 0.55 + 0.45 * math.sin(6.0 * v - 7.0 * t + 2.5 * u)
    dy = -(0.16 * w * s_) - 0.08 * w
    dx = 0.34 * w * (0.7 + 0.3 * math.sin(5.0 * v - 5.0 * t + 1.7 * u + 1.0))
    dz = 0.05 * w * math.sin(4 * v - 6 * t)
    return (FP[0] + x + dx, FP[1] + yb + dy, FP[2] + zb + dz)


def sash_pos(u, v, t):
    x = 0.28 + (u - 0.5) * 0.12
    w = v ** 1.2
    y = -0.12 - 0.5 * w + 0.12 * w * math.sin(8 * v - 9.0 * t + u)
    xx = x + 0.55 * w * (0.6 + 0.4 * math.sin(6 * v - 8.0 * t))
    z = 0.92 - 0.85 * v + 0.08 * w * math.sin(7 * v - 9.0 * t)
    return (FP[0] + xx, FP[1] + y, FP[2] + z)


cloak = Cloth('Cloak', matCloth, 10, 16, cloak_pos, lambda i, j: cream if j < 14 else hexc('#a8321f'))
sash = Cloth('Sash', matCloth, 3, 12, sash_pos, lambda i, j: red)

# ---------- birds ----------
matBird = vc_material('Bird', rough=0.6)
birds = Dyn('Birds', matBird)


def eagle_local(t, ph):
    m = M()
    br, br2 = hexc('#6a4528'), hexc('#4a2e1b')
    wh, ye, dk = hexc('#f4efe6'), hexc('#efbd2a'), hexc('#241812')
    m.cyl(0, 0, 0, 0.13, 0.4, 6, br, tf=RX(-math.pi / 2), r2=0.07)
    m.cyl(0, 0, 0, 0.13, 0.5, 6, br2, tf=RX(math.pi / 2), r2=0.03)
    m.sphere(0, 0.46, 0.02, 0.08, wh, rings=3, n=6)
    m.cyl(0, 0, 0, 0.04, 0.13, 4, ye, tf=chain(RX(-math.pi / 2), T(0, 0.52, -0.005)), r2=0.0)
    m.add([(-0.1, -0.45, 0), (0.1, -0.45, 0), (0.22, -0.85, 0.0), (-0.22, -0.85, 0.0)], [(0, 3, 2, 1)], wh)
    LEx = [0.08, 0.55, 1.05, 1.58]
    LEy = [0.32, 0.34, 0.22, -0.04]
    TEy = [-0.28, -0.36, -0.34, -0.26]
    for sg in (-1, 1):
        pts_le, pts_te = [], []
        for k in range(4):
            ang = 0.62 * math.sin(2 * math.pi * 1.4 * t + ph - 0.55 * k) + 0.1
            x = sg * LEx[k] * math.cos(ang)
            z = LEx[k] * math.sin(ang)
            pts_le.append((x, LEy[k], z))
            pts_te.append((x, TEy[k], z - 0.03))
        verts = pts_le + pts_te
        faces = [(k, k + 4, k + 5, k + 1) for k in range(3)]
        m.add(verts, faces, [br, br2, dk])
    return m


def birds_mesh(t):
    m = M()
    # hero eagle crossing the city
    px, py, pz = -80 + 15.5 * t, 64 + 9 * math.sin(0.5 * t), 4.0 + 3.0 * math.sin(0.8 * t)
    dx, dy = 15.5, 4.5 * math.cos(0.5 * t)
    hd = math.atan2(-dx, dy)
    e = eagle_local(t, 0.0)
    e.transform(chain(S(2.2, 2.2, 2.2), RY(-0.22 * math.sin(0.6 * t)), RZ(hd), T(px, py, pz)))
    m.merge(e)
    for k in range(5):
        ph = k * 1.7
        cx_, cy_ = -60 + 40 * k, 190 + 25 * math.sin(k)
        a_ = 0.35 * t + ph
        qx, qy, qz = cx_ + 22 * math.cos(a_), cy_ + 22 * math.sin(a_), 22 + 5 * math.sin(k * 2 + t * 0.5)
        hd2 = math.atan2(-(-22 * math.sin(a_)), 22 * math.cos(a_))
        e2 = eagle_local(t * 0.9, ph)
        e2.transform(chain(S(1.4, 1.4, 1.4), RZ(hd2), T(qx, qy, qz)))
        m.merge(e2)
    return m


# ---------- floating embers / dust ----------
embers = Dyn('Embers', matEmber)
EP = [(random.uniform(-9, 9), random.uniform(0, 26), random.uniform(-1, 9), random.uniform(0.03, 0.075), random.uniform(0, 6.3)) for _ in range(70)]


def embers_mesh(t):
    m = M()
    for k, (x, y, z, r, ph) in enumerate(EP):
        zz = (z + 0.8 * t) % 11.0 - 1.5
        m.sphere(x + 0.7 * math.sin(t * 0.8 + ph) - 0.5 * t, y + 0.5 * math.cos(t * 0.6 + ph) - 0.8 * t, zz, r, hexc('#ffb259'), rings=2, n=4)
    return m


def update(t):
    u = ease(t / 10.0)
    th = math.radians(lerp(-34, 76, u))
    r = lerp(5.0, 7.4, u)
    TG = (FP[0], FP[1], 1.55 + FP[2] - 0.35)
    pos = (TG[0] + r * math.sin(th) + 0.012 * math.sin(t * 2.3),
           TG[1] - r * math.cos(th) + 0.012 * math.cos(t * 1.9),
           TG[2] + lerp(0.5, 1.4, u) + 0.05 * math.sin(t * 1.1))
    k = ease(u * 1.15)
    tgt = (lerp(0.0, TG[0], k), lerp(FP[1] + 12, TG[1] - 0.2, k), lerp(-5.5, TG[2] - 0.05, k))
    aim(cam, pos, tgt)
    cam.data.dof.focus_distance = math.sqrt(sum((pos[i] - TG[i]) ** 2 for i in range(3)))
    cloak.update(t)
    sash.update(t)
    for f in flags:
        f.update(t)
    birds.set(birds_mesh(t))
    embers.set(embers_mesh(t))


render_frames(A, update)
