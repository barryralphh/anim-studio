"""Flat-vector stickman animation, pure shapes (PIL + numpy), no external assets.
Run: python3 flat.py out.mp4 [preview]
Draws at 1920x1080, downsamples to 1280x720, pipes to ffmpeg.
"""
import math, sys, subprocess, random
import numpy as np
from PIL import Image, ImageDraw, ImageChops, ImageFilter, ImageFont

W, H = 1920, 1080
OW, OH = 1280, 720
FPS = 24
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


# ---------------- helpers ----------------
def hexc(h, a=255):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)

def lerp(a, b, t): return a + (b - a) * t
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(t):
    t = clamp(t); return t * t * (3 - 2 * t)
def mixc(c1, c2, t): return tuple(int(lerp(c1[i], c2[i], t)) for i in range(len(c1)))

def vgrad(w, h, stops):
    """stops: [(pos 0..1, color)] vertical gradient -> RGBA Image"""
    ys = np.linspace(0, 1, h)
    out = np.zeros((h, 4))
    for ch in range(4):
        out[:, ch] = np.interp(ys, [s[0] for s in stops], [s[1][ch] if len(s[1]) > ch else 255 for s in stops])
    arr = np.repeat(out[:, None, :], w, axis=1).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')

def tapered(d, p0, p1, w0, w1, col):
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    pts = [(p0[0] + nx * w0 / 2, p0[1] + ny * w0 / 2), (p1[0] + nx * w1 / 2, p1[1] + ny * w1 / 2),
           (p1[0] - nx * w1 / 2, p1[1] - ny * w1 / 2), (p0[0] - nx * w0 / 2, p0[1] - ny * w0 / 2)]
    d.polygon(pts, fill=col)
    d.ellipse([p0[0] - w0 / 2, p0[1] - w0 / 2, p0[0] + w0 / 2, p0[1] + w0 / 2], fill=col)
    d.ellipse([p1[0] - w1 / 2, p1[1] - w1 / 2, p1[0] + w1 / 2, p1[1] + w1 / 2], fill=col)

def fk(root, a1, l1, a2, l2, f=1):
    """angles from straight-down, positive = forward"""
    p1 = (root[0] + f * l1 * math.sin(a1), root[1] + l1 * math.cos(a1))
    p2 = (p1[0] + f * l2 * math.sin(a2), p1[1] + l2 * math.cos(a2))
    return p1, p2


# ---------------- character ----------------
SKIN = hexc('#0b0810')
PANTS = hexc('#1a1422')
RIM = hexc('#f2b36b')

def draw_char(lean=0.1, legs=(0, 0, 0, 0), arms=(0.2, 0.4, -0.2, 0.3), hood='#e4492f',
              shoe='#d83a2e', S=320, f=1, tilt=0.0, eye='open', mouth='smile', hoodup=True,
              rim=True, dim=1.0):
    """returns (RGBA layer, anchor) with hip at anchor. legs=(t1,s1,t2,s2) arms=(u1,f1,u2,f2)"""
    R = int(S * 1.25)
    layer = Image.new('RGBA', (2 * R, 2 * R), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    c = (R, R)
    hc = hexc(hood)
    hc = tuple(int(v * dim) for v in hc[:3]) + (255,)
    hd = tuple(int(v * 0.72) for v in hc[:3]) + (255,)
    pc = tuple(int(v * dim) for v in PANTS[:3]) + (255,)
    sc = hexc(shoe)
    tl = 0.24 * S
    tor = 0.30 * S
    hr = 0.125 * S
    sh = (c[0] + f * tor * math.sin(lean), c[1] - tor * math.cos(lean))
    # back arm / back leg
    def arm(u, fa, col):
        e, h = fk((sh[0], sh[1] + 0.02 * S), u, 0.2 * S, fa, 0.19 * S, f)
        tapered(d, (sh[0], sh[1] + 0.02 * S), e, 0.06 * S, 0.05 * S, col)
        tapered(d, e, h, 0.05 * S, 0.045 * S, col)
        d.ellipse([h[0] - 0.035 * S, h[1] - 0.035 * S, h[0] + 0.035 * S, h[1] + 0.035 * S], fill=SKIN)
    def leg(t, s, col, shoe_col):
        k, a = fk(c, t, tl, s, tl, f)
        tapered(d, c, k, 0.07 * S, 0.05 * S, col)
        tapered(d, k, a, 0.05 * S, 0.042 * S, col)
        fx = a[0] + f * 0.055 * S
        d.rounded_rectangle([min(a[0] - f * 0.02 * S, fx + f * 0.04 * S), a[1] - 0.012 * S,
                             max(a[0] - f * 0.02 * S, fx + f * 0.04 * S), a[1] + 0.04 * S], radius=int(0.02 * S), fill=shoe_col)
    backhood = tuple(int(v * 0.8) for v in hc[:3]) + (255,)
    arm(arms[2], arms[3], hd)
    leg(legs[2], legs[3], tuple(int(v * 0.8) for v in pc[:3]) + (255,), tuple(int(v * 0.8) for v in sc[:3]) + (255,))
    # torso (hoodie)
    hw, bw = 0.085 * S, 0.095 * S
    nx, ny = math.cos(lean) * f, math.sin(lean)
    hem = 0.07 * S
    tp = [(sh[0] - nx * hw, sh[1] - ny * hw * f), (sh[0] + nx * hw, sh[1] + ny * hw * f),
          (c[0] + nx * bw, c[1] + ny * bw * f + hem), (c[0] - nx * bw, c[1] - ny * bw * f + hem)]
    d.polygon(tp, fill=hc)
    # hoodie pocket line + shade
    d.polygon([tp[0], (sh[0] - f * 0.01 * S, sh[1]), (c[0] - f * 0.01 * S, c[1] + hem), tp[3]], fill=hd)
    d.line([(c[0] + f * 0.01 * S, c[1] - 0.03 * S), (c[0] + f * 0.06 * S, c[1] + 0.03 * S)], fill=hd, width=max(2, int(S / 90)))
    leg(legs[0], legs[1], pc, sc)
    # head
    neck = (sh[0] + f * 0.01 * S, sh[1] - 0.02 * S)
    hcx = neck[0] + f * math.sin(lean + tilt) * (hr * 0.9)
    hcy = neck[1] - hr * 0.95
    if hoodup:
        d.ellipse([hcx - f * hr * 0.55 - hr * 0.85, hcy + hr * 0.15 - hr * 0.85,
                   hcx - f * hr * 0.55 + hr * 0.85, hcy + hr * 0.15 + hr * 0.85], fill=hd)
        d.polygon([(neck[0] - 0.1 * S, neck[1] + 0.02 * S), (neck[0] + 0.1 * S, neck[1] + 0.02 * S),
                   (neck[0] + f * 0.02 * S, neck[1] - hr * 0.5)], fill=hc)
    d.ellipse([hcx - hr, hcy - hr, hcx + hr, hcy + hr], fill=SKIN)
    # face
    ex, ey = hcx + f * hr * 0.45, hcy - hr * 0.1
    er = hr * 0.14
    if eye == 'open':
        d.ellipse([ex - er, ey - er * 1.2, ex + er, ey + er * 1.2], fill=(250, 244, 235, 255))
    elif eye == 'closed':
        d.arc([ex - er * 1.4, ey - er * 1.2, ex + er * 1.4, ey + er * 1.2], 0, 180, fill=(250, 244, 235, 255), width=max(2, int(S / 100)))
    elif eye == 'angry':
        d.chord([ex - er * 2, ey - er * 1.2, ex + er * 2, ey + er * 1.3], 0, 180, fill=(250, 244, 235, 255))
    if mouth == 'smile':
        mx, my = hcx + f * hr * 0.4, hcy + hr * 0.38
        d.arc([mx - hr * 0.22, my - hr * 0.16, mx + hr * 0.22, my + hr * 0.16], 20, 160, fill=(250, 244, 235, 255), width=max(2, int(S / 100)))
    elif mouth == 'flat':
        mx, my = hcx + f * hr * 0.4, hcy + hr * 0.42
        d.line([mx - hr * 0.15, my, mx + hr * 0.15, my], fill=(250, 244, 235, 255), width=max(2, int(S / 100)))
    # front arm
    arm(arms[0], arms[1], hc)
    if rim:
        a = layer.split()[3]
        a2 = ImageChops.offset(a, int(S * 0.012) * f, -int(S * 0.012))
        rl = Image.new('RGBA', layer.size, RIM)
        rl.putalpha(ImageChops.subtract(a2, a))
        layer = Image.alpha_composite(rl, layer)
    return layer, c


def paste_char(img, pos, **kw):
    layer, c = draw_char(**kw)
    img.alpha_composite(layer, (int(pos[0] - c[0]), int(pos[1] - c[1])))


def run_pose(ph, amp):
    """returns legs, arms, lean for run/stand blend"""
    s = math.sin(ph)
    t1 = amp * 0.95 * s
    t2 = -t1
    k1 = t1 - amp * (0.9 * max(0, math.sin(ph + 1.3)) + 0.15)
    k2 = t2 - amp * (0.9 * max(0, math.sin(ph + 1.3 + math.pi)) + 0.15)
    u1, u2 = -amp * 0.9 * s + 0.15, amp * 0.9 * s + 0.15
    f1, f2 = u1 + amp * 1.2 + 0.2, u2 + amp * 1.2 + 0.2
    return (t1, k1, t2, k2), (u1, f1, u2, f2), 0.08 + 0.22 * amp


def grounded_hip(x, ground, legs, S):
    tl = 0.24 * S
    low = max(tl * math.cos(legs[0]) + tl * math.cos(legs[1]), tl * math.cos(legs[2]) + tl * math.cos(legs[3]))
    return (x, ground - low)


# ---------------- scene A: bus stop at sunset ----------------
def bg_busstop():
    img = vgrad(W, 900, [(0, hexc('#8a5a9a')), (0.35, hexc('#b3688f')), (0.62, hexc('#e8906a')), (1, hexc('#f4b06a'))])
    full = Image.new('RGBA', (W, H), hexc('#3d2e4a'))
    full.alpha_composite(img, (0, 0))
    # sun glow + rays
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    sx, sy = 1560, 700
    for r in range(380, 0, -20):
        gd.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(255, 220, 150, int(30 * (1 - r / 380) + 6)))
    full.alpha_composite(glow.filter(ImageFilter.GaussianBlur(25)))
    rays = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rays)
    for i in range(9):
        a = math.radians(200 + i * 17)
        a2 = a + math.radians(5)
        rd.polygon([(sx, sy), (sx + 2500 * math.cos(a), sy + 2500 * math.sin(a)),
                    (sx + 2500 * math.cos(a2), sy + 2500 * math.sin(a2))], fill=(255, 235, 190, 26))
    full.alpha_composite(rays)
    d = ImageDraw.Draw(full)
    d.ellipse([sx - 60, sy - 60, sx + 60, sy + 60], fill=hexc('#ffe9b0'))
    # clouds
    for cx, cy, cw in [(500, 250, 700), (1300, 330, 600), (150, 420, 260)]:
        cl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        cd = ImageDraw.Draw(cl)
        cd.ellipse([cx - cw / 2, cy - 18, cx + cw / 2, cy + 18], fill=(120, 80, 140, 200))
        cd.ellipse([cx - cw / 2.4, cy - 8, cx + cw / 2.4, cy + 12], fill=(250, 190, 140, 160))
        full.alpha_composite(cl.filter(ImageFilter.GaussianBlur(3)))
    # silhouette houses
    rnd = random.Random(4)
    col = hexc('#59405f')
    x = -60
    while x < W + 60:
        w = rnd.randint(260, 420); h = rnd.randint(150, 260)
        d.rectangle([x, 760 - h, x + w, 790], fill=col)
        if rnd.random() < 0.7:
            d.polygon([(x - 10, 760 - h), (x + w / 2, 760 - h - rnd.randint(90, 150)), (x + w + 10, 760 - h)], fill=col)
        for wx in range(x + 30, x + w - 40, 90):
            if rnd.random() < 0.3:
                d.rectangle([wx, 760 - h + 50, wx + 36, 760 - h + 90], fill=hexc('#f6c46c'))
        x += w - 30
    # road / sidewalk
    d.rectangle([0, 790, W, 880], fill=hexc('#4a3858'))
    d.rectangle([0, 880, W, H], fill=hexc('#8d7787'))
    d.rectangle([0, 880, W, 892], fill=hexc('#b49aa0'))
    d.line([0, 840, W, 840], fill=hexc('#7a6285'), width=4)
    # pole + wires
    d.rectangle([1500, 380, 1516, 800], fill=hexc('#3f2f46'))
    d.rectangle([1440, 400, 1580, 410], fill=hexc('#3f2f46'))
    for off in (0, 40):
        pts = [(x, 420 + off + 60 * math.sin(math.pi * ((x % 1500) / 1500)) * 0.5 + (x - 960) ** 2 / 20000) for x in range(-20, W + 20, 20)]
        d.line(pts, fill=hexc('#35283d'), width=3)
    # shelter
    d.rectangle([300, 640, 1000, 662], fill=hexc('#4a3a55'))
    for x in (320, 980):
        d.rectangle([x, 660, x + 12, 880], fill=hexc('#4a3a55'))
    d.rectangle([332, 662, 980, 860], fill=(110, 90, 130, 70))
    d.rectangle([420, 780, 760, 830], fill=hexc('#6f5d78'))
    # sign
    d.rectangle([1040, 640, 1050, 880], fill=hexc('#6c5a75'))
    d.ellipse([1005, 590, 1085, 670], fill=hexc('#e9f3ee'), outline=hexc('#3a8f8c'), width=8)
    return full


def draw_bus(img, x0):
    d = ImageDraw.Draw(img)
    y0, y1 = 560, 880
    L = 900
    d.rounded_rectangle([x0, y0, x0 + L, y1 - 30], radius=18, fill=hexc('#efe6d4'))
    d.rectangle([x0, y0 + 205, x0 + L, y0 + 235], fill=hexc('#2f9a98'))
    d.rectangle([x0, y1 - 60, x0 + L, y1 - 25], fill=hexc('#3a2f4a'))
    for i in range(5):
        wx = x0 + 40 + i * 150
        d.rectangle([wx, y0 + 40, wx + 130, y0 + 150], fill=hexc('#5a456a'))
        d.polygon([(wx, y0 + 40), (wx + 50, y0 + 40), (wx + 10, y0 + 150), (wx, y0 + 150)], fill=hexc('#6d5780'))
    # door
    dx = x0 + L - 130
    d.rectangle([dx, y0 + 30, dx + 100, y1 - 30], fill=hexc('#f7d890'))
    d.rectangle([dx + 90, y0 + 30, dx + 100, y1 - 30], fill=hexc('#8f8a98'))
    d.ellipse([dx + 30, y0 + 70, dx + 62, y0 + 102], fill=hexc('#3a2f4a'))
    d.rectangle([dx + 22, y0 + 98, dx + 70, y0 + 150], fill=hexc('#8a7a90'))
    d.rectangle([x0, y0, x0 + 18, y0 + 160], fill=hexc('#d85a45'))
    # shade overlay
    sh = Image.new('RGBA', img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.rectangle([x0, y0 + 190, x0 + L, y1 - 30], fill=(60, 30, 80, 55))
    img.alpha_composite(sh)
    d = ImageDraw.Draw(img)
    for wxx in (x0 + 170, x0 + 720):
        d.ellipse([wxx - 62, y1 - 92, wxx + 62, y1 + 32], fill=hexc('#2b2236'))
        d.ellipse([wxx - 34, y1 - 64, wxx + 34, y1 + 4], fill=hexc('#a9a3b0'))
        d.ellipse([wxx - 10, y1 - 40, wxx + 10, y1 - 20], fill=hexc('#6b6475'))


def frame_A(t, bg):
    img = bg.copy()
    bx = 700 + (0.5 * 300 * (t - 1.3) ** 2 if t > 1.3 else 0)
    draw_bus(img, bx)
    S = 430
    ground = 975
    # runner
    T1 = 2.5
    if t < T1:
        k = ease(t / T1)
        x = -120 + 1400 * k
        v = 1400 * 6 * (t / T1) * (1 - t / T1) / T1
    else:
        x = 1280; v = 0
    amp = clamp(v / 520)
    ph = x / 80
    legs, arms, lean = run_pose(ph, amp)
    arms = list(arms)
    eye, mouth = 'open', 'smile'
    if t > 1.6:  # reach for the bus, arm up
        up = ease((t - 1.6) / 0.5)
        arms[0] = lerp(arms[0], 2.5, up); arms[1] = lerp(arms[1], 2.8, up)
    if t > 3.0:
        dr = ease((t - 3.0) / 0.8)
        arms[0] = lerp(arms[0], 0.05, dr); arms[1] = lerp(arms[1], 0.1, dr)
        lean = lerp(lean, 0.32, dr)
        eye, mouth = 'angry', 'flat'
    hip = grounded_hip(x, ground, legs, S)
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([x - 120, ground - 12, x + 120, ground + 14], fill=(30, 15, 40, 110))
    img.alpha_composite(sh)
    paste_char(img, hip, lean=lean, legs=legs, arms=tuple(arms), S=S, eye=eye, mouth=mouth)
    return img


# ---------------- scene B: bus interior ----------------
def draw_interior(t):
    img = Image.new('RGBA', (W, H), hexc('#3c3550'))
    d = ImageDraw.Draw(img)
    # window strip
    win = vgrad(W, 300, [(0, hexc('#9b6fa3')), (0.5, hexc('#eeaa80')), (1, hexc('#ffd08a'))])
    img.alpha_composite(win, (0, 215))
    rnd = random.Random(8)
    houses = []
    x = 0
    while x < W * 3:
        w = rnd.randint(200, 340); h = rnd.randint(120, 230)
        houses.append((x, w, h, rnd.random() < 0.5)); x += w + rnd.randint(30, 120)
    sp = 260 * (0.5 + 0.5 * ease(t / 1.2))
    off = sp * t
    span = x
    for hx, w, h, roof in houses:
        for rep in (0, 1):
            px = hx - (off % span) + rep * span
            if -400 < px < W + 400:
                d.rectangle([px, 500 - h, px + w, 520], fill=hexc('#6d4f7c'))
                if roof:
                    d.polygon([(px - 8, 500 - h), (px + w / 2, 500 - h - 90), (px + w + 8, 500 - h)], fill=hexc('#6d4f7c'))
                d.rectangle([px + 40, 500 - h + 45, px + 76, 500 - h + 85], fill=hexc('#f6c46c'))
    d.rectangle([0, 500, W, 520], fill=hexc('#f1c070'))
    for px in range(60, W, 430):
        d.rectangle([px, 215, px + 40, 520], fill=hexc('#3a3150'))
    d.rectangle([0, 150, W, 215], fill=hexc('#4a4260'))
    d.rectangle([0, 175, W, 190], fill=hexc('#6a5f82'))
    # wall under windows and floor
    d.rectangle([0, 520, W, 880], fill=hexc('#4b4563'))
    d.rectangle([0, 880, W, H], fill=hexc('#5c5068'))
    # seats
    for sx in (180, 760, 1340):
        d.polygon([(sx, 600), (sx + 150, 560), (sx + 150, 840), (sx, 880)], fill=hexc('#3f8f8a'))
        d.polygon([(sx + 110, 600), (sx + 150, 560), (sx + 160, 560), (sx + 120, 610)], fill=hexc('#6cc0b4'))
        d.polygon([(sx - 110, 780), (sx + 360, 780), (sx + 410, 830), (sx - 60, 830)], fill=hexc('#4fa59d'))
        d.rectangle([sx + 100, 830, sx + 160, 920], fill=hexc('#2c2638'))
        d.polygon([(sx - 20, 925), (sx + 300, 925), (sx + 330, 950), (sx + 10, 950)], fill=hexc('#2c2638'))
    return img


def frame_B(t):
    img = draw_interior(t)
    S = 560
    bob = math.sin(t * 9) * 2.5
    seatY = 800
    pos = [(310, '#b58a86', 0.78, 'closed'), (1470, '#7e88a6', 0.78, 'open')]
    for px, col, dim, eye in pos:
        paste_char(img, (px, seatY - 24 + bob * 0.5), lean=0.0, legs=(1.45, 0.05, 1.45, 0.05), arms=(0.6, 1.4, 0.5, 1.3),
                   hood=col, shoe='#2c2638', S=S, eye=eye, dim=dim, hoodup=False, rim=True,
                   tilt=0.15 if eye == 'closed' else 0.0)
    blink = 'closed' if (int(t * 24) % 70) in (0, 1, 2) else 'open'
    look = 0.0 if t < 3.5 else 0.12
    paste_char(img, (900, seatY - 24 + bob), lean=0.0, legs=(1.45, 0.05, 1.45, 0.05), arms=(0.55, 1.35, 0.5, 1.3), S=S,
               eye=blink, mouth='smile' if t < 3.5 else 'flat', tilt=look)
    d = ImageDraw.Draw(img)
    for px in (690, 1250):
        d.rectangle([px, 120, px + 14, 960], fill=hexc('#e0b43a'))
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    for i in range(4):
        x0 = 150 + i * 480 + math.sin(t * 2 + i) * 6
        sd.polygon([(x0, 520), (x0 + 120, 520), (x0 - 160, 1000), (x0 - 330, 1000)], fill=(255, 220, 160, 22))
    img.alpha_composite(sh)
    return img


# ---------------- post ----------------
def make_vignette():
    yy, xx = np.mgrid[0:OH, 0:OW]
    r = np.sqrt(((xx - OW / 2) / (OW / 2)) ** 2 + ((yy - OH / 2) / (OH / 2)) ** 2)
    return (1 - 0.42 * np.clip(r - 0.55, 0, 1) ** 1.5)[:, :, None]

VIG = make_vignette()
PILLFONT = ImageFont.truetype(FONT, 30)

def post(img, t, label, fade):
    im = img.convert('RGB').resize((OW, OH), Image.LANCZOS)
    if label:
        pl = Image.new('RGBA', (OW, OH), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pl)
        tw = pd.textlength(label, font=PILLFONT)
        pd.rounded_rectangle([34, 40, 34 + tw + 40, 90], radius=25, fill=(20, 12, 24, 215), outline=(190, 150, 70, 255), width=2)
        pd.text((54, 47), label, font=PILLFONT, fill=(238, 190, 80, 255))
        im = Image.alpha_composite(im.convert('RGBA'), pl).convert('RGB')
    a = np.asarray(im).astype(np.float32)
    a *= VIG
    rng = np.random.default_rng(int(t * 24))
    a += rng.normal(0, 3.0, a.shape[:2])[:, :, None]
    a *= fade
    a[:46] = 0; a[-46:] = 0
    return np.clip(a, 0, 255).astype(np.uint8)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else 'flat.mp4'
    prev = len(sys.argv) > 2
    N = 240
    bgA = bg_busstop()
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{OW}x{OH}',
                          '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-pix_fmt', 'yuv420p', out],
                         stdin=subprocess.PIPE)
    frames = [0, 40, 70, 100, 130, 180, 235] if prev else range(N)
    for i in frames:
        t = i / FPS
        if i < 120:
            img = frame_A(t, bgA); label = None
        else:
            img = frame_B(t - 5.0); label = 'DAY 1  •  6 MPH'
        fade = min(1, t / 0.6, (10 - t) / 0.6, abs(t - 5.0) / 0.25 if abs(t - 5.0) < 0.25 else 1)
        p.stdin.write(post(img, t, label, clamp(fade)).tobytes())
    p.stdin.close(); p.wait()


if __name__ == '__main__':
    main()
