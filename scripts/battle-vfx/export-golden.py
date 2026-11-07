#!/usr/bin/env python3
"""Export golden samples of the procedural skills for the Swift port check (scripts/battle-procedural-regression.swift).
For each skill and sample time: primitive count, per-kind counts, the sum of every number, and the first primitives in full."""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import procfx

GEO = dict(caster=(140.0, 330.0), casterFoot=(140.0, 400.0), targets=[((520.0, 300.0), (520.0, 400.0)), ((300.0, 310.0), (300.0, 400.0))], ground=400.0)
TIMES = [0.07, 0.2, 0.37, 0.55, 0.8, 1.1, 1.45, 1.9]
SKILLS = ['starlightPulse', 'dragonSoulWard', 'dragonScaleWard', 'runeSlash', 'runeWard', 'battleRune', 'dragonFlame', 'dragonOrder', 'healMicro', 'healStandard', 'healStrong', 'rally', 'sweep', 'natural20', 'shieldDome', 'hitBlade', 'hitGreat', 'hitBow', 'hitStaff', 'hitClaw', 'hitAmbush', 'hitWard', 'shieldBreak', 'deathBurst', 'projBow', 'projStaff', 'projArcher', 'projDragon', 'shieldShell', 'shieldShellHit', 'hitSlime', 'hitWolf', 'hitArrowM', 'hitStone', 'hitTroll', 'hitDragon', 'deathSlime', 'deathWolf', 'deathGoblin', 'deathStone', 'deathTroll', 'deathDragon', 'playerDown', 'downAura', 'revive']


def flat(p):
    k = p[0]
    if k == 'g': return [0, *p[1:5], *p[5], p[6]]
    if k == 'r': return [1, *p[1:6], *p[6], p[7], p[8] if len(p) > 8 else 0.0]
    if k == 'e': return [2, *p[1:6], *p[6], p[7]]
    if k == 'a': return [3, *p[1:8], *p[8], p[9]]
    if k == 'k':
        pts, ws, col, a, mode, soft = p[1:7]
        return [4, len(pts), *[v for q in pts for v in q], *ws, *col, a, 1.0 if mode == 'add' else 0.0, soft]
    if k == 'f': return [5, *p[1], p[2]]
    raise ValueError(k)


def main():
    out = {'geometry': {'caster': GEO['caster'], 'casterFoot': GEO['casterFoot'], 'targets': GEO['targets'], 'ground': GEO['ground']}, 'times': TIMES, 'skills': {}}
    for sid in SKILLS:
        gen = procfx.GENERATORS[sid]; samples = []
        for t in TIMES:
            prims = gen(t, GEO); fl = [flat(p) for p in prims]
            kinds = [0] * 6
            for f in fl: kinds[int(f[0])] += 1
            total = sum(sum(f) for f in fl)
            samples.append({'t': t, 'count': len(fl), 'kinds': kinds, 'sum': total, 'head': [[round(v, 9) for v in f] for f in fl[:6]]})
        out['skills'][sid] = samples
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'procedural-golden.json')
    with open(path, 'w') as fh: json.dump(out, fh, separators=(',', ':'))
    print(path, os.path.getsize(path) // 1024, 'KB', {s: [x['count'] for x in v] for s, v in out['skills'].items()})


if __name__ == '__main__':
    main()
