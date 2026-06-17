"""
Vector-style icon/graphic generator (white & blue palette) for the EEG presentation.
Renders crisp transparent PNG assets with Pillow: stylized brain, head profile with
brain, EEG electrode cap, EEG multi-channel waves, neuron, and a running athlete.
"""
import math
import os
from PIL import Image, ImageDraw, ImageFilter

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(OUT, exist_ok=True)

# ---- Palette (RGB) ----
NAVY   = (10, 38, 71)
BLUE   = (24, 86, 160)
MID    = (46, 111, 183)
SKY    = (74, 144, 217)
CYAN   = (0, 178, 216)
LIGHT  = (170, 205, 240)
PALE   = (224, 236, 250)
WHITE  = (255, 255, 255)

SS = 4  # supersampling factor for smooth edges


def _canvas(w, h):
    return Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))


def _finish(img, w, h):
    return img.resize((w, h), Image.LANCZOS)


def _c(color, a=255):
    return (color[0], color[1], color[2], a)


# ---------------------------------------------------------------------------
# EEG multi-channel wave strip (transparent) — looks like a recording trace
# ---------------------------------------------------------------------------
def eeg_waves(path, w=2400, h=700, channels=5, color=MID, lw=5, seed=1):
    img = _canvas(w, h)
    d = ImageDraw.Draw(img)
    W, H = w * SS, h * SS
    rng = _rng(seed)
    band = H / (channels + 1)
    for ch in range(channels):
        baseline = band * (ch + 1)
        # mix of frequencies + random spikes -> EEG-like
        f1 = 6 + rng() * 6
        f2 = 14 + rng() * 14
        f3 = 28 + rng() * 18
        ph1, ph2, ph3 = rng() * 6.28, rng() * 6.28, rng() * 6.28
        amp = band * 0.34
        pts = []
        steps = 1400
        for i in range(steps + 1):
            x = W * i / steps
            t = i / steps * math.pi * 2
            y = (math.sin(t * f1 + ph1) * 0.6
                 + math.sin(t * f2 + ph2) * 0.28
                 + math.sin(t * f3 + ph3) * 0.16)
            # occasional sharp spike
            if rng() > 0.992:
                y += (rng() - 0.5) * 3.2
            pts.append((x, baseline - y * amp))
        col = color if ch % 2 == 0 else SKY
        d.line(pts, fill=_c(col, 235), width=lw * SS, joint="curve")
    img = _finish(img, w, h)
    img.save(path)


def _rng(seed):
    state = [seed * 2654435761 % 2147483647]

    def r():
        state[0] = (state[0] * 1103515245 + 12345) % 2147483648
        return state[0] / 2147483648
    return r


# ---------------------------------------------------------------------------
# Single elegant pulse line with a glow (accent)
# ---------------------------------------------------------------------------
def pulse_line(path, w=2400, h=300, color=CYAN, lw=6):
    img = _canvas(w, h)
    d = ImageDraw.Draw(img)
    W, H = w * SS, h * SS
    mid = H / 2
    pts = []
    steps = 1000
    for i in range(steps + 1):
        x = W * i / steps
        frac = i / steps
        # flat line with a few QRS-like heartbeat/EEG spikes
        y = 0
        for center in (0.18, 0.45, 0.72):
            dd = (frac - center)
            y += math.exp(-(dd * 60) ** 2) * (1.0 if center != 0.45 else -1.3)
        y += math.sin(frac * 90) * 0.06
        pts.append((x, mid - y * H * 0.34))
    glow = _canvas(w, h)
    dg = ImageDraw.Draw(glow)
    dg.line(pts, fill=_c(color, 120), width=lw * SS * 4, joint="curve")
    glow = glow.filter(ImageFilter.GaussianBlur(SS * 6))
    img.alpha_composite(glow)
    d.line(pts, fill=_c(color, 255), width=lw * SS, joint="curve")
    img = _finish(img, w, h)
    img.save(path)


# ---------------------------------------------------------------------------
# Stylized brain (top/3-4 view) with gyri — clean line-art symbol
# ---------------------------------------------------------------------------
def brain(path, size=1400, color=BLUE, lw=9, fill_alpha=22):
    img = _canvas(size, size)
    d = ImageDraw.Draw(img)
    S = size * SS
    cx, cy = S / 2, S / 2
    rx, ry = S * 0.40, S * 0.33

    # lumpy outline resembling a brain
    outline = []
    for i in range(0, 361, 2):
        t = math.radians(i)
        bump = (0.075 * math.sin(6 * t) + 0.04 * math.sin(11 * t + 1.0)
                + 0.025 * math.sin(17 * t))
        x = cx + rx * (1 + bump) * math.cos(t)
        y = cy + ry * (1 + bump) * math.sin(t)
        outline.append((x, y))
    # soft fill
    d.polygon(outline, fill=_c(SKY, fill_alpha))
    d.line(outline + [outline[0]], fill=_c(color, 255), width=lw * SS, joint="curve")

    # central sulcus (vertical wavy division)
    cs = []
    for i in range(0, 101):
        f = i / 100
        y = cy - ry * 0.82 + ry * 1.64 * f
        x = cx + math.sin(f * math.pi * 5) * S * 0.018
        cs.append((x, y))
    d.line(cs, fill=_c(color, 230), width=int(lw * SS * 0.8), joint="curve")

    # gyri — C-shaped curves on each hemisphere
    def gyrus(side, yoff, scale, arc=1.0):
        pts = []
        for i in range(0, 101):
            a = math.pi * (0.15 + 1.7 * (i / 100)) * arc
            r = S * 0.11 * scale
            x = cx + side * (S * 0.10 + r * math.sin(a))
            y = cy + yoff + r * (math.cos(a) - 0.3)
            pts.append((x, y))
        d.line(pts, fill=_c(color, 210), width=int(lw * SS * 0.7), joint="curve")

    for side in (-1, 1):
        for k, yoff in enumerate((-ry * 0.5, -ry * 0.05, ry * 0.42)):
            gyrus(side, yoff, 1.0 + 0.15 * k, arc=1.0)

    # brainstem hint at bottom
    bs = [(cx - S * 0.03, cy + ry * 0.9), (cx + S * 0.03, cy + ry * 0.9),
          (cx + S * 0.05, cy + ry * 1.12), (cx - S * 0.05, cy + ry * 1.12)]
    d.line([bs[0], bs[3]], fill=_c(color, 220), width=int(lw * SS * 0.8))
    d.line([bs[1], bs[2]], fill=_c(color, 220), width=int(lw * SS * 0.8))

    img = _finish(img, size, size)
    img.save(path)


# ---------------------------------------------------------------------------
# Head profile (side view) containing a brain + small wave — iconic neuro symbol
# ---------------------------------------------------------------------------
def head_profile(path, size=1400, color=BLUE, lw=9):
    img = _canvas(size, size)
    d = ImageDraw.Draw(img)
    S = size * SS
    cx, cy = S * 0.52, S * 0.5
    R = S * 0.34

    # head silhouette facing left (skull arc + face profile)
    head = []
    # back & top of skull
    for i in range(0, 181, 3):
        t = math.radians(i)
        x = cx - R * math.cos(t) * 1.02
        y = cy - R * math.sin(t)
        head.append((x, y))
    # forehead -> nose -> chin (simple profile on the left)
    head += [
        (cx - R * 1.02, cy + R * 0.02),
        (cx - R * 1.08, cy + R * 0.30),   # brow
        (cx - R * 1.20, cy + R * 0.46),   # nose tip
        (cx - R * 1.05, cy + R * 0.55),   # under nose
        (cx - R * 1.10, cy + R * 0.74),   # lips/chin
        (cx - R * 0.95, cy + R * 0.92),   # chin
        (cx - R * 0.55, cy + R * 1.02),   # jaw
        (cx + R * 0.10, cy + R * 1.04),   # neck base
    ]
    # neck down
    head += [(cx + R * 0.10, cy + R * 1.35), (cx + R * 0.55, cy + R * 1.35)]
    # right side back down
    head += [(cx + R * 0.62, cy + R * 0.6), (cx + R * 1.0, cy + R * 0.1)]
    d.polygon(head, fill=_c(SKY, 16))
    d.line(head, fill=_c(color, 255), width=lw * SS, joint="curve")

    # brain inside the skull (smaller lumpy blob)
    bx, by = cx - R * 0.12, cy - R * 0.18
    brx, bry = R * 0.55, R * 0.42
    bout = []
    for i in range(0, 361, 4):
        t = math.radians(i)
        bump = 0.10 * math.sin(6 * t) + 0.05 * math.sin(11 * t)
        x = bx + brx * (1 + bump) * math.cos(t)
        y = by + bry * (1 + bump) * math.sin(t)
        bout.append((x, y))
    d.line(bout + [bout[0]], fill=_c(MID, 240), width=int(lw * SS * 0.8), joint="curve")
    # a couple of gyri swirls
    for off in (-bry * 0.4, bry * 0.15):
        sw = []
        for i in range(0, 101):
            f = i / 100
            a = f * math.pi * 2.2
            r = brx * 0.42 * (1 - f * 0.4)
            sw.append((bx + math.cos(a) * r, by + off + math.sin(a) * r * 0.7))
        d.line(sw, fill=_c(SKY, 220), width=int(lw * SS * 0.6), joint="curve")

    img = _finish(img, size, size)
    img.save(path)


# ---------------------------------------------------------------------------
# EEG electrode cap (top view, 10-20 system dots) — clear EEG symbol
# ---------------------------------------------------------------------------
def electrode_cap(path, size=1400, color=BLUE, lw=8):
    img = _canvas(size, size)
    d = ImageDraw.Draw(img)
    S = size * SS
    cx, cy = S / 2, S * 0.52
    R = S * 0.40

    # head outline with a small nose notch at top
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=_c(color, 255),
              width=lw * SS, fill=_c(SKY, 14))
    nose = [(cx - R * 0.12, cy - R * 0.98), (cx, cy - R * 1.16),
            (cx + R * 0.12, cy - R * 0.98)]
    d.line(nose, fill=_c(color, 255), width=lw * SS, joint="curve")

    # electrode positions on concentric rings
    dots = [(0, 0)]
    for ring_r, n in ((0.45, 8), (0.78, 12)):
        for k in range(n):
            a = math.pi * 2 * k / n + (0.2 if ring_r > 0.6 else 0)
            dots.append((ring_r * math.cos(a), ring_r * math.sin(a)))
    # connecting grid lines (subtle)
    for (ax, ay) in dots:
        d.line([(cx, cy), (cx + ax * R, cy + ay * R)],
               fill=_c(LIGHT, 120), width=int(lw * SS * 0.4))
    # electrodes
    er = S * 0.028
    for (ax, ay) in dots:
        x, y = cx + ax * R, cy + ay * R
        col = CYAN if (ax == 0 and ay == 0) else MID
        d.ellipse([x - er, y - er, x + er, y + er], fill=_c(col, 255),
                  outline=_c(WHITE, 255), width=int(lw * SS * 0.4))

    img = _finish(img, size, size)
    img.save(path)


# ---------------------------------------------------------------------------
# Neuron with dendrites and axon terminals
# ---------------------------------------------------------------------------
def neuron(path, size=1400, color=BLUE, lw=7):
    img = _canvas(size, size)
    d = ImageDraw.Draw(img)
    S = size * SS
    cx, cy = S * 0.40, S * 0.5
    soma = S * 0.085
    rng = _rng(7)

    # dendrites (branching) on the left/top
    def branch(x, y, ang, length, depth):
        if depth == 0:
            return
        x2 = x + math.cos(ang) * length
        y2 = y + math.sin(ang) * length
        d.line([(x, y), (x2, y2)], fill=_c(color, 235),
               width=max(int(lw * SS * depth * 0.5), SS), joint="curve")
        for s in (-1, 1):
            branch(x2, y2, ang + s * (0.5 + rng() * 0.4),
                   length * 0.62, depth - 1)

    for a in (2.4, 3.0, 3.5, 4.0):
        branch(cx, cy, a, S * 0.16, 3)

    # axon to the right with terminal buttons
    ax_end = cx + S * 0.42
    d.line([(cx + soma, cy), (ax_end, cy + S * 0.04)],
           fill=_c(MID, 240), width=int(lw * SS * 1.2), joint="curve")
    for s in (-1, 0, 1):
        ea = 0.0 + s * 0.5
        tx = ax_end + math.cos(ea) * S * 0.08
        ty = cy + S * 0.04 + math.sin(ea) * S * 0.08
        d.line([(ax_end, cy + S * 0.04), (tx, ty)], fill=_c(MID, 240),
               width=int(lw * SS * 0.9), joint="curve")
        d.ellipse([tx - S * 0.02, ty - S * 0.02, tx + S * 0.02, ty + S * 0.02],
                  fill=_c(CYAN, 255))

    # soma
    d.ellipse([cx - soma, cy - soma, cx + soma, cy + soma],
              fill=_c(SKY, 60), outline=_c(color, 255), width=lw * SS)
    nuc = soma * 0.4
    d.ellipse([cx - nuc, cy - nuc, cx + nuc, cy + nuc], fill=_c(BLUE, 255))

    img = _finish(img, size, size)
    img.save(path)


# ---------------------------------------------------------------------------
# Running athlete silhouette (sports pictogram, filled)
# ---------------------------------------------------------------------------
def runner(path, size=1400, color=BLUE):
    img = _canvas(size, size)
    d = ImageDraw.Draw(img)
    S = size * SS

    def P(x, y):
        return (x * S, y * S)

    def limb(p1, p2, p3, width):
        w = int(width * S)
        d.line([p1, p2, p3], fill=_c(color, 255), width=w, joint="curve")
        for p in (p1, p2, p3):
            d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2],
                      fill=_c(color, 255))

    # leaning-forward dynamic runner, facing right
    shoulder = P(0.50, 0.34)
    hip = P(0.44, 0.58)
    # torso
    limb(shoulder, P(0.47, 0.46), hip, 0.085)
    # back arm (driving back)
    limb(shoulder, P(0.38, 0.40), P(0.32, 0.50), 0.052)
    # front arm (driving forward & up)
    limb(shoulder, P(0.60, 0.40), P(0.66, 0.31), 0.052)
    # front leg (high knee, bent)
    limb(hip, P(0.56, 0.62), P(0.52, 0.50), 0.066)
    # back leg (extended, pushing off)
    limb(hip, P(0.40, 0.74), P(0.30, 0.84), 0.066)
    # head
    hr = 0.062 * S
    hc = P(0.545, 0.26)
    d.ellipse([hc[0] - hr, hc[1] - hr, hc[0] + hr, hc[1] + hr], fill=_c(color, 255))

    # motion accent lines behind
    for i, yy in enumerate((0.36, 0.46, 0.56)):
        d.line([P(0.10, yy), P(0.30 - i * 0.02, yy)],
               fill=_c(SKY, 170), width=int(0.018 * S), joint="curve")

    img = _finish(img, size, size)
    img.save(path)


# ---------------------------------------------------------------------------
# Radial / circular EEG wave ring (decorative hero element)
# ---------------------------------------------------------------------------
def wave_ring(path, size=1600, color=SKY, lw=5):
    img = _canvas(size, size)
    d = ImageDraw.Draw(img)
    S = size * SS
    cx, cy = S / 2, S / 2
    base = S * 0.34
    rng = _rng(3)
    f1, f2 = 18, 40
    ph1, ph2 = rng() * 6.28, rng() * 6.28
    pts = []
    for i in range(0, 721):
        t = math.radians(i / 2)
        wob = (math.sin(t * f1 + ph1) * 0.045
               + math.sin(t * f2 + ph2) * 0.02)
        if rng() > 0.985:
            wob += (rng() - 0.5) * 0.18
        r = base * (1 + wob)
        pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    d.line(pts, fill=_c(color, 230), width=lw * SS, joint="curve")
    img = _finish(img, size, size)
    img.save(path)


if __name__ == "__main__":
    eeg_waves(os.path.join(OUT, "eeg_waves_wide.png"), w=2600, h=520, channels=4, seed=2)
    eeg_waves(os.path.join(OUT, "eeg_waves_block.png"), w=1700, h=1000, channels=6, seed=5)
    pulse_line(os.path.join(OUT, "pulse.png"))
    brain(os.path.join(OUT, "brain.png"))
    brain(os.path.join(OUT, "brain_light.png"), color=WHITE, fill_alpha=0)
    head_profile(os.path.join(OUT, "head_profile.png"))
    head_profile(os.path.join(OUT, "head_profile_light.png"), color=WHITE)
    electrode_cap(os.path.join(OUT, "electrode_cap.png"))
    neuron(os.path.join(OUT, "neuron.png"))
    runner(os.path.join(OUT, "runner.png"))
    runner(os.path.join(OUT, "runner_light.png"), color=WHITE)
    wave_ring(os.path.join(OUT, "wave_ring.png"))
    print("assets generated in", OUT)
