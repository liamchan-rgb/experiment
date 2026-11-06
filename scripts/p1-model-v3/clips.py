"""Poses for every P1 cell: idle, walk-start 1-2, jog (walk 1-8), walk-stop 1-2."""
import math

# Jog: right foot, q = poses since its contact: (forward u in ground px, lift, toe pitch; + = toes down).
# Stance feet move back exactly 12 ground px per pose = the game's 24 units per 8-pose cycle.
LEG = [(12, 0, -.15), (0, 0, 0), (-12, 0, .35), (-16, 6, .9), (-10, 12, 1.1), (2, 12, .5), (11, 7, 0), (14, 2, -.2)]
BOB = [0, 2, 0, -2]
SWING, BEND, LEAN, TWIST = .55, .9, .12, .12
ENTRY_PHASE = 0   # walk-start 2 hands over to jog pose 0 (right contact)
EXIT_PHASE = 7


def arms(swing_r, bend_r, swing_l, bend_l):
    return {'R': (swing_r, bend_r), 'L': (swing_l, bend_l)}


def jog(p):
    c = math.cos(2 * math.pi * p / 8)
    out = {}
    for side, sign in (('R', -1), ('L', 1)):
        swing = SWING * c * sign
        out[side] = (swing, BEND + .4 * max(0, swing) / SWING)
    return dict(bob=BOB[p % 4], lean=LEAN, twist=-TWIST * c,
                legs={'R': LEG[p % 8], 'L': LEG[(p + 4) % 8]}, arms=out)


def pose(clip, n):
    if clip == 'idle':
        return dict(bob=0, lean=0, twist=0, legs={'R': (2, 0, 0), 'L': (-2, 0, 0)}, arms=arms(.05, .25, .05, .25))
    if clip == 'walk':
        return jog(n - 1)
    if clip == 'walk-start':
        if n == 1:   # weight shifts onto the left foot, right knee lifts
            return dict(bob=1, lean=.06, twist=.04, legs={'R': (3, 5, .35), 'L': (-2, 0, 0)}, arms=arms(-.2, .55, .2, .6))
        return dict(bob=0, lean=.1, twist=.09, legs={'R': (10, 5, -.1), 'L': (-8, 0, .35)}, arms=arms(-.4, .8, .4, .95))
    if clip == 'walk-stop':
        if n == 1:   # brake on the right foot, left catches up
            return dict(bob=2, lean=.04, twist=-.04, legs={'R': (5, 0, 0), 'L': (-4, 4, .3)}, arms=arms(.2, .6, -.2, .6))
        return dict(bob=1, lean=0, twist=0, legs={'R': (2, 0, 0), 'L': (-2, 1, 0)}, arms=arms(.08, .35, .08, .35))
    raise ValueError(clip)
