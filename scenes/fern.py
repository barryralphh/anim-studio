
# ===================== STYLISED DIORAMA ISLAND (original) =====================
A = parse_args()
random.seed(21)
sc = setup_render(A, samples=48)

SUN = vnorm((0.55, -0.5, 0.66))
sky_world(SUN, zenith=hexc('#3a86dc'), horizon=hexc('#d3ecff'), ground=hexc('#d3ecff'),
          glow=hexc('#ffe2b0'), sun_col=hexc('#fff6e0'), glow_pow=6.0, glow_amt=0.5, sun_amt=8.0,
          strength=1.05, hz_pow=0.7, z_scale=1.4)
make_sun(SUN, (1.0, 0.93, 0.82), 3.6, angle=0.05)
add_glare(mix_=-0.7, threshold=1.0, size=6)
cam = make_camera(30.0, 6.0)

mat = vc_material('Land', rough=0.8, spec=0.12)
matW = vc_material('Props', rough=0.6, spec=0.2)
matCloud = vc_material('Cloud', rough=1.0, spec=0.0)

R = 11.0
N = 60
PH = [(random.uniform(0, 6.28), random.uniform(0, 6.28), random.uniform(0, 6.28)) for _ in range(6)]


def fbm(x, y):
    s, amp, fr = 0.0, 1.0, 0.33
    for k in range(5):
        p = PH[k]
        s += amp * math.sin(fr * x + p[0] + 1.3 * math.sin(fr * 0.7 * y + p[1])) * math.sin(fr * y * 1.1 + p[2] + 0.9 * math.sin(fr * 0.8 * x + p[0]))
        amp *= 0.5
        fr *= 2.0
    return s / 1.6


MOUNTS = [(-1.5, 2.9, 4.4, 1.9), (3.3, 0.9, 3.0, 1.6), (-3.6, -0.4, 1.6, 1.4)]
VX, VY = -3.7, -2.9


def H(x, y):
    r = math.hypot(x, y)
    n = fbm(x, y)
    land = 1 - smooth(4.4, 8.0, r + 1.8 * fbm(x * 0.7 + 3, y * 0.7))
    h = -1.2 + land * (2.6 + 0.9 * n)
    for mx, my, amp, sg in MOUNTS:
        h += amp * math.exp(-((x - mx) ** 2 + (y - my) ** 2) / (2 * sg * sg)) * land
    pd = math.hypot(x - VX, y - VY)
    h = lerp(h, 0.6, (1 - smooth(0.9, 2.2, pd)) * land)
    return h


def hh(i, j): return ((i * 73856093) ^ (j * 19349663)) % 1000 / 1000.0


def disc(i, j):
    u, v = -1 + 2 * i / N, -1 + 2 * j / N
    return (R * u * math.sqrt(1 - v * v / 2), R * v * math.sqrt(1 - u * u / 2))


SEA_Z = -0.2
raw, zz, pts = {}, {}, {}
for i in range(N + 1):
    for j in range(N + 1):
        x, y = disc(i, j)
        h = H(x, y)
        raw[(i, j)] = h
        edge = (i in (0, N) or j in (0, N))
        z = h if h > 0 else SEA_Z + (0 if edge else (hh(i, j) - 0.5) * 0.07)
        zz[(i, j)] = z
        pts[(i, j)] = (x, y, z)

C = {k: hexc(v) for k, v in dict(deep='#1b68bd', mid='#1f8fd0', shal='#33c0d8', foam='#9bece8', sand='#f5dca0',
                                  g1='#82db58', g2='#66c24c', hi='#3e9e4c', rock='#a08d80', rock2='#716873', snow='#ffffff').items()}


def tcol(h, i, j):
    k = 1.0 + (hh(i, j) - 0.5) * 0.1
    if h < -0.95: c = C['deep']
    elif h < -0.45: c = C['mid']
    elif h < -0.12: c = C['shal']
    elif h < 0.04: c = C['foam']
    elif h < 0.36: c = C['sand']
    elif h < 1.7: c = C['g1'] if hh(i + 7, j + 3) > 0.45 else C['g2']
    elif h < 2.5: c = C['hi']
    elif h < 3.7: c = C['rock']
    elif h < 4.3: c = C['rock2']
    else: c = C['snow']
    return shade(c, k)


land = M()
for i in range(N):
    for j in range(N):
        a_, b_, c_, d_ = (i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)
        tris = [(a_, b_, c_), (a_, c_, d_)] if (i + j) % 2 == 0 else [(a_, b_, d_), (b_, c_, d_)]
        for tr in tris:
            ah = sum(raw[q] for q in tr) / 3.0
            land.tri(pts[tr[0]], pts[tr[1]], pts[tr[2]], tcol(ah, i, j))

# perimeter skirt
per = [(i, 0) for i in range(N)] + [(N, j) for j in range(N)] + [(i, N) for i in range(N, 0, -1)] + [(0, j) for j in range(N, 0, -1)]
levels = [SEA_Z, -1.0, -1.9, -3.0]
bands = [hexc('#2aa7c9'), hexc('#c9925a'), hexc('#8c6a4c'), hexc('#5d5360')]
for k in range(len(per)):
    p0, p1 = pts[per[k]], pts[per[(k + 1) % len(per)]]
    for b in range(3):
        land.quad((p0[0], p0[1], levels[b]), (p0[0], p0[1], levels[b + 1]), (p1[0], p1[1], levels[b + 1]), (p1[0], p1[1], levels[b]),
                  shade(bands[b + 1] if b else bands[0], 1.0 + (hh(k, b) - 0.5) * 0.08))
land.to_obj('Land', mat)

# ---------- trees ----------
props = M()
greens = ['#2f9e44', '#37b24d', '#40c057', '#51cf66', '#2b8a3e']
placed = 0
tries = 0
while placed < 300 and tries < 6000:
    tries += 1
    x, y = random.uniform(-R, R), random.uniform(-R, R)
    if x * x + y * y > 70:
        continue
    h = H(x, y)
    if not (0.45 < h < 2.35):
        continue
    if math.hypot(x - VX, y - VY) < 1.9:
        continue
    if fbm(x * 1.3 + 9, y * 1.3 - 4) < -0.15:
        continue
    s_ = random.uniform(0.28, 0.5)
    gc = hexc(random.choice(greens)) if h < 1.8 else hexc('#1f7a4a')
    props.box(0, 0, h - 0.05, 0.1 * s_ * 2, 0.1 * s_ * 2, 0.35 * s_ * 2, hexc('#7a4f2a'), tf=T(x, y, 0))
    props.cyl(0, 0, h + 0.2 * s_ * 2, 0.5 * s_, 0.8 * s_, 6, gc, r2=0.0, tf=T(x, y, 0))
    props.cyl(0, 0, h + 0.55 * s_ * 2, 0.38 * s_, 0.7 * s_, 6, shade(gc, 1.12), r2=0.0, tf=T(x, y, 0))
    placed += 1

# ---------- village ----------
hz_ = H(VX, VY)
wall_cols = ['#fff3dd', '#ffe3b8', '#f7f0ff', '#ffd9d0']
roof_cols = ['#e8554e', '#f08c3a', '#d9423f']
for k in range(8):
    ang = k * 2.4
    hx, hy = VX + 1.15 * math.cos(ang) * (0.4 + 0.12 * k), VY + 1.1 * math.sin(ang) * (0.4 + 0.12 * k)
    rot = random.uniform(0, 3.14)
    bw, bd, bh = random.uniform(0.5, 0.75), random.uniform(0.5, 0.75), random.uniform(0.4, 0.6)
    tf = chain(RZ(rot), T(hx, hy, 0))
    props.box(0, 0, hz_, bw, bd, bh, hexc(random.choice(wall_cols)), tf=tf)
    props.box(0, 0, hz_ + bh, bw + 0.14, bd + 0.14, 0.4, hexc(random.choice(roof_cols)), tf=tf, top=(0.0, 1.0))
props.box(0, 0, hz_, 0.55, 0.55, 1.2, hexc('#fff3dd'), tf=T(VX + 0.1, VY + 0.1, 0))
props.cyl(VX + 0.1, VY + 0.1, hz_ + 1.2, 0.5, 0.7, 4, hexc('#d9423f'), r2=0.0, tf=chain(T(-VX - 0.1, -VY - 0.1, 0), RZ(0.78), T(VX + 0.1, VY + 0.1, 0)))
props.to_obj('Props', matW)

# ---------- route ----------
def catmull(p, n):
    out = []
    P = [p[0]] + p + [p[-1]]
    for s in range(len(p) - 1):
        p0, p1, p2, p3 = P[s], P[s + 1], P[s + 2], P[s + 3]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[c]) + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2 + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3) for c in range(2)))
    out.append(p[-1])
    return out


ROUTE = catmull([(VX + 0.4, VY + 0.3), (-2.2, -1.7), (-0.5, -2.0), (0.8, -0.5), (-0.1, 1.0), (-1.2, 2.2), (-1.5, 3.0)], 10)
RZ_ = [(x, y, max(H(x, y), 0.0) + 0.16) for x, y in ROUTE]
matDot = vc_material('Dots', rough=0.4, spec=0.4)
dots = Dyn('Dots', matDot)
pin = Dyn('Pin', matDot)
matShip = vc_material('Ship', rough=0.6)
ship = Dyn('Ship', matShip)
clouds = Dyn('Clouds', matCloud)

CL = [(random.uniform(-13, 13), random.uniform(-13, 13), random.uniform(4.6, 6.2), random.uniform(0.8, 1.3), random.uniform(0.25, 0.5)) for _ in range(7)]


def clouds_mesh(t):
    m = M()
    white = (1.0, 1.0, 1.0)
    for k, (cx, cy, cz, s_, sp) in enumerate(CL):
        x = ((cx + sp * t * 1.5 + 15) % 30) - 15
        for q, (ox, oy, oz, rr) in enumerate([(0, 0, 0, 1.0), (0.9, 0.2, -0.1, 0.8), (-0.9, -0.1, -0.15, 0.75), (0.3, 0.5, 0.3, 0.7), (-0.4, -0.5, 0.1, 0.65)]):
            m.sphere(x + ox * s_, cy + oy * s_, cz + oz * s_, rr * s_, white, rings=3, n=8, sz=0.7)
    return m


def ship_mesh(t):
    m = M()
    th = 0.55 - 0.16 * t
    rr = 9.3
    x, y = rr * math.cos(th), rr * math.sin(th)
    hd = th - math.pi / 2
    bob = 0.04 * math.sin(t * 2.2)
    tf = chain(RZ(hd - math.pi / 2), T(x, y, SEA_Z + 0.12 + bob))
    m.box(0, 0, 0, 0.5, 1.2, 0.26, hexc('#8a5a34'), tf=tf, top=(1.15, 1.0))
    m.cyl(0, 0.62, 0, 0.25, 0.26, 4, hexc('#8a5a34'), tf=chain(RZ(math.pi / 4), tf), r2=0.0)
    m.box(0, -0.05, 0.26, 0.05, 0.05, 1.3, hexc('#5a3a20'), tf=tf)
    m.tri((0, -0.02, 0.45), (0, -0.02, 1.5), (0, 0.55, 0.5), hexc('#fffaf0'), tf=tf)
    m.tri((0, -0.08, 0.5), (0, -0.08, 1.35), (0, -0.5, 0.5), hexc('#fff1d0'), tf=tf)
    m.tri((0, -0.05, 1.55), (0, -0.05, 1.3), (0, 0.22, 1.42), hexc('#e8554e'), tf=tf)
    for k in range(6):
        w_ = 0.18 + 0.05 * k
        m.quad((-w_, -0.7 - 0.4 * k, 0.02), (w_, -0.7 - 0.4 * k, 0.02), (w_ * 1.1, -0.95 - 0.4 * k, 0.02), (-w_ * 1.1, -0.95 - 0.4 * k, 0.02), (0.85, 0.97, 1.0) if k < 5 else (0.7, 0.9, 1.0), tf=tf)
    return m


def route_head(t):
    f = clamp((t - 2.0) / 6.0)
    idx = f * (len(RZ_) - 1)
    k = min(int(idx), len(RZ_) - 2)
    u = idx - k
    a_, b_ = RZ_[k], RZ_[k + 1]
    return tuple(lerp(a_[i], b_[i], u) for i in range(3))


def route_mesh(t):
    m = M()
    f = ease((t - 2.0) / 6.0) if False else clamp((t - 2.0) / 6.0)
    n = int(f * (len(RZ_) - 1))
    for k in range(0, n, 2):
        x, y, z = RZ_[k]
        pop = clamp((t - 2.0 - k * (6.0 / (len(RZ_) - 1))) / 0.4)
        r_ = 0.085 * ease(pop) * (1.0 + 0.4 * (1 - pop))
        m.sphere(x, y, z, r_ + 0.001, (1.0, 1.0, 1.0), rings=2, n=6)
    return m


def pin_mesh(t):
    m = M()
    x, y, z = route_head(t)
    hov = 0.25 + 0.12 * abs(math.sin(t * 4.0)) + (0.15 if t > 8 else 0)
    red = hexc('#ff3b4a')
    m.cyl(0, 0, 0, 0.2, 0.5, 8, red, tf=chain(RX(math.pi), T(0, 0, 0.5 + hov)), r2=0.0)
    m.sphere(0, 0, 0.5 + hov, 0.2, red, rings=3, n=8)
    m.sphere(0, 0, 0.62 + hov, 0.08, (1, 1, 1), rings=2, n=6)
    m.transform(T(x, y, z))
    return m


def update(t):
    u = ease(t / 10.0)
    az = math.radians(lerp(212, 262, u))
    r = lerp(27.0, 19.5, u)
    z = lerp(15.5, 9.8, u)
    head = route_head(t)
    k = 0.40 * u
    tgt = (lerp(0.0, head[0], k), lerp(0.0, head[1], k), 0.4)
    pos = (r * math.cos(az), r * math.sin(az), z)
    aim(cam, pos, tgt)
    clouds.set(clouds_mesh(t))
    ship.set(ship_mesh(t))
    dots.set(route_mesh(t))
    pin.set(pin_mesh(t))


render_frames(A, update)
