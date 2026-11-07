"""Reference implementation of the battle hit feel (presentation only).

This module is the SPEC. `Sources/Game/MeadowBattleHitFeel.swift` is a literal port, so the
formulas here use only simple closed forms. Layout units are the 760-wide battle canvas units;
`a` is seconds since the impact fired, `r = max(0, a - HOLD)` is seconds since the hit-stop released.
Y grows downward. `direction` is +1 when the blow travels to the right (hero -> monster).
"""
import math

HOLD = 0.10                       # shared with MeadowBattleImpactClock's 0.10 s contact pose hold
TIERS = ('light', 'medium', 'heavy')
INTENSITY = {'light': 0.7, 'medium': 1.0, 'heavy': 1.45}
FLARE_RADIUS = {'light': 34.0, 'medium': 46.0, 'heavy': 64.0}
SPARKS = {'light': 14, 'medium': 22, 'heavy': 34}
LEAVES = {'light': 3, 'medium': 6, 'heavy': 10}


def clamp01(x): return min(1.0, max(0.0, x))
def smooth(x): t = clamp01(x); return t * t * (3 - 2 * t)
def ease_out(x): t = clamp01(x); return 1 - (1 - t) ** 3
def ease_in(x): t = clamp01(x); return t * t


def fraction(i, salt):
    """Deterministic pseudo-random in [0, 1): identical on every platform and frame rate."""
    return ((i * 73 + salt * 37 + (i * i) * 11) % 101) / 100.0


def classify(damage, killed=False):
    """Light up to 5, medium 6-11, heavy 12+; a killing blow is at least medium."""
    tier = 'light' if damage <= 5 else 'medium' if damage <= 11 else 'heavy'
    if killed and tier == 'light':
        tier = 'medium'
    return tier


def release(a): return max(0.0, a - HOLD)


# ---- camera -------------------------------------------------------------------------------
def camera(a, tier, direction=1.0):
    """(dx, dy, zoom, rotation_radians) applied to the whole battle world (HUD stays still)."""
    k = INTENSITY[tier]
    r = release(a)
    if a < HOLD:                                   # frozen: a small punch-in that holds
        return 0.0, 0.0, 0.032 * k * ease_out(a / 0.03), 0.0
    zoom = 0.032 * k * math.exp(-r * 9.0)
    dx = direction * 6.0 * k * math.exp(-r * 10.0) * math.cos(r * 34.0)
    dy = -2.2 * k * math.exp(-r * 12.0) * math.sin(r * 40.0 + 0.6)
    rot = direction * 0.0062 * k * math.exp(-r * 10.0) * math.sin(r * 30.0)
    return dx, dy, zoom, rot


# ---- monster reaction ---------------------------------------------------------------------
def knockback(a, tier, canvas_width=760.0):
    """Horizontal displacement of the struck monster, in canvas units (+ = away from the attacker)."""
    k = INTENSITY[tier]
    r = release(a)
    if a < HOLD:
        return 0.0
    distance = canvas_width * 0.025 * (0.8 + 0.5 * (k - 0.7))
    return distance * 1.15 * (1 - math.exp(-r * 30.0)) * math.exp(-max(0.0, r - 0.10) * 5.5)


def squash(a, tier):
    """(scale_x, scale_y) about the monster's feet."""
    k = INTENSITY[tier]
    if a < HOLD:
        q = 0.6 * ease_out(a / 0.03)
    else:
        r = release(a)
        q = math.exp(-r * 10.0) * math.cos(r * 20.0)
    return 1 + 0.05 * k * q, 1 - 0.07 * k * q


def flash(a):
    """Hit-flash alpha on the struck monster's hit-mask (and a faint whole-silhouette tint)."""
    if a < 0:
        return 0.0
    if a < 0.04:
        return 1.0
    return 1 - smooth((a - 0.04) / 0.08)


# ---- impact graphics ----------------------------------------------------------------------
def flare(a, tier):
    """Short, sharp contact flare. Returns (radius, alpha) or None."""
    if a < 0 or a > 0.14:
        return None
    R = FLARE_RADIUS[tier]
    grow = 0.55 + 0.45 * ease_out(a / 0.04)
    alpha = 1.0 if a < 0.06 else 1 - ease_in((a - 0.06) / 0.08)
    return R * grow, alpha


def ring(a, tier):
    """Expanding shock ring. Returns (radius, width, alpha) or None."""
    life = 0.26
    if a < 0 or a > life:
        return None
    R = FLARE_RADIUS[tier]
    t = a / life
    return 8 + R * 2.1 * ease_out(t), 4.0 * (1 - t) + 0.6, (1 - t) ** 1.3 * 0.85


def sparks(a, tier, direction=1.0):
    """Directional streaks. Each: (head_x, head_y, tail_x, tail_y, width, alpha, heat) relative to impact."""
    out = []
    k = INTENSITY[tier]
    for i in range(SPARKS[tier]):
        life = 0.16 + 0.22 * fraction(i, 3)
        if a < 0 or a >= life:
            continue
        angle = (0.0 if direction > 0 else math.pi) + (fraction(i, 1) - 0.5) * 2 * math.radians(70)
        angle -= direction * 0.2                                # slight upward bias
        speed = (320 + 340 * fraction(i, 2)) * k
        drag = 6.0
        travel = speed * (1 - math.exp(-a * drag)) / drag
        gravity = 380.0 if fraction(i, 4) > 0.55 else 0.0
        hx = math.cos(angle) * travel
        hy = math.sin(angle) * travel + 0.5 * gravity * a * a
        now = speed * math.exp(-a * drag)
        length = max(4.0, min(46.0, now * 0.055))
        tx = hx - math.cos(angle) * length
        ty = hy - math.sin(angle) * length - 0.0
        life_t = a / life
        out.append((hx, hy, tx, ty, 3.2 - 2.0 * life_t, (1 - life_t) ** 0.8, clamp01(life_t * 1.4)))
    return out


def dust(a, tier):
    """Ground puffs at the monster's feet after the hit-stop releases. Each: (dx, rx, ry, alpha)."""
    r = release(a)
    if a < HOLD or r > 0.45:
        return []
    k = INTENSITY[tier]
    out = []
    for i in range(3 if tier == 'light' else 5):
        side = (i - (1 if tier == 'light' else 2)) * 0.9
        t = ease_out(r / 0.36)
        out.append((side * 22 * k * t, (10 + 36 * t) * (0.8 + 0.2 * k), (10 + 36 * t) * 0.26, 0.22 * (1 - clamp01(r / 0.45))))
    return out


def leaves(a, tier, direction=1.0):
    """Foliage shed by the Forest Warden. Each: (x, y, rotation, size, alpha, tone) relative to impact."""
    out = []
    k = INTENSITY[tier]
    for i in range(LEAVES[tier]):
        life = 0.55 + 0.5 * fraction(i, 6)
        if a < 0 or a >= life:
            continue
        angle = (0.0 if direction > 0 else math.pi) + (fraction(i, 8) - 0.5) * 2 * math.radians(80) - direction * 0.5
        speed = (90 + 110 * fraction(i, 9)) * k
        t = a
        x = math.cos(angle) * speed * (1 - math.exp(-t * 3.2)) / 3.2 + math.sin(t * 7 + i) * 6
        y = math.sin(angle) * speed * (1 - math.exp(-t * 3.2)) / 3.2 + 120.0 * t * t * (0.5 + fraction(i, 10)) + math.cos(t * 6 + i) * 3
        out.append((x, y, t * (6 + 8 * fraction(i, 11)) * (1 if i % 2 else -1), 5 + 4 * fraction(i, 12), 1 - ease_in(a / life), i % 3))
    return out


def number(a, tier):
    """Damage number pop. Returns (scale, y_offset, alpha, font_size) or None."""
    if a < 0 or a > 0.9:
        return None
    base = {'light': 22.0, 'medium': 25.0, 'heavy': 30.0}[tier]
    pop = 1.7 - 0.7 * ease_out(a / 0.09) if a < 0.09 else 1.0
    rise = 34.0 * ease_out(min(a, 0.5) / 0.5)
    alpha = 1.0 if a < 0.55 else 1 - smooth((a - 0.55) / 0.35)
    return pop, -rise, alpha, base


def haptic(tier):
    """UIImpactFeedbackGenerator style and intensity."""
    return {'light': ('light', 0.7), 'medium': ('medium', 0.85), 'heavy': ('heavy', 1.0)}[tier]
