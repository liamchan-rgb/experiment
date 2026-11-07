"""Status effect samples kept in step with production cue requests.

The offline scene compositor uses older sampled attachment defaults for its
positioning. Replace only the status timing/geometry from the current requests
so previews cannot display a heal or shield before the production cue.
"""
from __future__ import annotations

import math


def smooth(value: float) -> float:
    t = max(0.0, min(1.0, value))
    return t * t * (3.0 - 2.0 * t)


def _recovery_pulse(age: float) -> float:
    return smooth(age / 0.24) if age < 0.46 else 1.0 - smooth((age - 0.46) / 1.34)


def _recovery_samples(age: float) -> tuple[list[dict], list[list[dict]]]:
    if age < 0.0 or age >= 1.80:
        return [], [[], []]

    power = _recovery_pulse(age)
    motes = []
    for i in range(26):
        birth = ((i // 2) % 7) * 0.065
        elapsed = age - birth
        life = 1.12 + ((i // 2) % 4) * 0.10
        if elapsed < 0.0 or elapsed >= life:
            continue
        u = elapsed / life
        angle = u * math.pi * 4.0 - age * 3.4 + (i % 2) * math.pi
        radius = 42.0 - u * 12.0
        motes.append({
            "id": i,
            "x": math.cos(angle) * radius,
            "y": -14.0 - u * 156.0 + math.sin(angle) * 4.0,
            "size": 8.0 if i % 6 == 0 else 4.0,
            "alpha": math.sin(math.pi * u) * power * 0.9,
        })

    ribbons = []
    front = min(1.12, max(0.0, age / 0.62))
    for strand in range(2):
        points = []
        for i in range(97):
            u = i / 96.0
            angle = u * math.pi * 4.0 - age * 3.4 + strand * math.pi
            radius = 42.0 - u * 12.0
            fade = smooth(u / 0.06) * (1.0 - smooth((u - 0.93) / 0.07)) * smooth((front - u) / 0.12)
            points.append({
                "x": math.cos(angle) * radius,
                "y": -14.0 - u * 156.0 + math.sin(angle) * 4.0,
                "depth": math.sin(angle),
                "alpha": power * fade,
            })
        ribbons.append(points)
    return motes, ribbons


def _shield_opacity(request: dict) -> float:
    if request.get("shield", 0) <= 0:
        return 0.0
    birth = request.get("birth")
    if birth is None:
        return 0.68 + math.sin(request.get("time", 0.0) * 3.0) * 0.025
    birth = max(0.0, float(birth))
    spawn = smooth(birth / 0.12)
    flare = smooth(birth / 0.12) if birth < 0.12 else 1.0 - smooth((birth - 0.12) / 0.28)
    breathing = smooth(birth / 0.4)
    return max(0.0, min(1.0, 0.68 * spawn + flare * 0.14 + math.sin(request.get("time", 0.0) * 3.0) * 0.025 * breathing))


def retime_status_sample(sample: dict, request: dict) -> dict:
    """Return the sampled attachment with its current receipt/cue timing."""
    sample = dict(sample)
    sample["shieldOpacity"] = _shield_opacity(request)
    age = request.get("recoveryAge")
    if age is None:
        sample["recoveryPower"] = 0.0
        sample["recovery"] = []
        sample["ribbons"] = [[], []]
        sample.pop("recoveryTier", None)
        return sample

    age = float(age)
    sample["recoveryPower"] = _recovery_pulse(age) if 0.0 <= age < 1.80 else 0.0
    sample["recovery"], sample["ribbons"] = _recovery_samples(age)
    if request.get("recoveryTier") is not None:
        sample["recoveryTier"] = request["recoveryTier"]
    return sample
