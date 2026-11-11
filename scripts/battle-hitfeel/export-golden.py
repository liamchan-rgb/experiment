#!/usr/bin/env python3
"""Export golden samples of the hit-feel reference for the Swift port's pure regression.

Usage: python3 -I scripts/battle-hitfeel/export-golden.py   (writes scripts/battle-hitfeel/golden.json)
"""
import json, sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
import hitfeel as hf

AGES = [-0.02, 0.0, 0.01, 0.03, 0.05, 0.08, 0.099, 0.1, 0.101, 0.12, 0.15, 0.2, 0.26, 0.3, 0.45, 0.6, 0.9, 1.2]

def listify(value):
    if value is None: return None
    if isinstance(value, tuple): return [listify(v) for v in value]
    if isinstance(value, list): return [listify(v) for v in value]
    return value

def main():
    golden = {'ages': AGES, 'classify': [], 'tiers': {}}
    for damage in (0, 1, 5, 6, 11, 12, 29):
        for killed in (False, True):
            golden['classify'].append({'damage': damage, 'killed': killed, 'tier': hf.classify(damage, killed)})
    for tier in hf.TIERS:
        rows = []
        for a in AGES:
            row = {'age': a,
                   'camera': {str(d): listify(hf.camera(a, tier, d)) for d in (1, -1)},
                   'knockback': hf.knockback(a, tier, 760.0), 'knockback1000': hf.knockback(a, tier, 1000.0),
                   'squash': listify(hf.squash(a, tier)), 'flash': hf.flash(a),
                   'flare': listify(hf.flare(a, tier)), 'ring': listify(hf.ring(a, tier)),
                   'sparks': {str(d): listify(hf.sparks(a, tier, d)) for d in (1, -1)},
                   'dust': listify(hf.dust(a, tier)),
                   'leaves': {str(d): listify(hf.leaves(a, tier, d)) for d in (1, -1)},
                   'number': listify(hf.number(a, tier))}
            rows.append(row)
        golden['tiers'][tier] = {'rows': rows, 'haptic': list(hf.haptic(tier)),
                                 'constants': {'intensity': hf.INTENSITY[tier], 'flareRadius': hf.FLARE_RADIUS[tier],
                                               'sparkCount': hf.SPARKS[tier], 'leafCount': hf.LEAVES[tier]}}
    path = Path(__file__).parent / 'golden.json'
    path.write_text(json.dumps(golden, separators=(',', ':')) + '\n')
    print('wrote', path, path.stat().st_size, 'bytes')

if __name__ == '__main__':
    main()
