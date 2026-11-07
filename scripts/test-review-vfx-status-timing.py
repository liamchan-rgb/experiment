#!/usr/bin/env python3
"""Regression checks for delayed status layers in the offline scene composer."""
from review_vfx_status_timing import retime_status_sample


def sample():
    return {
        "shieldOpacity": 0.7,
        "recoveryPower": 1.0,
        "recovery": [{"id": 99, "x": 0, "y": 0, "size": 8, "alpha": 1}],
        "ribbons": [[{"x": 0, "y": 0, "depth": 1, "alpha": 1}]],
    }


before = retime_status_sample(sample(), {"time": 1.0, "shield": 0})
assert before["shieldOpacity"] == 0
assert before["recoveryPower"] == 0 and before["recovery"] == []
assert before["ribbons"] == [[], []]

at_cue = retime_status_sample(sample(), {
    "time": 1.0, "shield": 6, "birth": 0.0, "recoveryAge": 0.0,
})
assert at_cue["shieldOpacity"] == 0
assert at_cue["recoveryPower"] == 0
assert not any(mote["alpha"] > 0 for mote in at_cue["recovery"])
assert not any(point["alpha"] > 0 for strand in at_cue["ribbons"] for point in strand)

ramping = retime_status_sample(sample(), {
    "time": 1.06, "shield": 6, "birth": 0.06, "recoveryAge": 0.06,
})
assert 0 < ramping["shieldOpacity"] < 0.68
assert ramping["recoveryPower"] > 0
assert any(mote["alpha"] > 0 for mote in ramping["recovery"])
assert any(point["alpha"] > 0 for strand in ramping["ribbons"] for point in strand)

settled = retime_status_sample(sample(), {
    "time": 1.2, "shield": 6, "birth": 0.2, "recoveryAge": 0.2,
})
assert settled["shieldOpacity"] > 0.68
assert settled["recoveryPower"] > ramping["recoveryPower"]

expired = retime_status_sample(sample(), {
    "time": 3.0, "shield": 0, "recoveryAge": 1.80,
})
assert expired["shieldOpacity"] == 0 and expired["recoveryPower"] == 0
assert expired["recovery"] == [] and expired["ribbons"] == [[], []]
print("Offline status timing passed: no pre-cue healing/shield, smooth birth, production recovery helix.")
