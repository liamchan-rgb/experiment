"""Battle formations (reference for Sources/Game/MeadowBattleFormation.swift).
The world is 1000Z x 600Z; Z grows with the number of units so they keep their size and the camera sees more of the field.
Left team: heroes. Right team: monsters, or in PvP the other heroes, mirrored (they face left)."""

# Hero slots in order of filling, for each world zoom (feet, world units). Front of the formation is towards the centre.
HEROES = {
    1.0: [(165, 420), (315, 505)],
    1.25: [(520, 560), (470, 690), (330, 600), (290, 720)],
    1.45: [(610, 650), (570, 770), (460, 600), (430, 700), (400, 800), (290, 650), (260, 760)],
}
MONSTERS = {
    1.0: [(650, 395), (835, 510), (600, 585)],
    1.25: [(820, 560), (1010, 690), (1040, 520)],
    1.45: [(940, 640), (1140, 770), (1180, 590)],
}


def zoom(players, foes, pvp):
    n = max(len(players), len(foes) if pvp else 0)
    if n <= 2 and (pvp or len(foes) <= 3): return 1.0
    if n <= 4: return 1.25
    return 1.45


def layout(players, foes, pvp):
    Z = zoom(players, foes, pvp); W = 1000 * Z
    feet = {}; mirrored = set()
    for i, p in enumerate(players): feet[p] = HEROES[Z][i]
    if pvp:
        for i, p in enumerate(foes):
            x, y = HEROES[Z][i]; feet[p] = (W - x, y); mirrored.add(p)
    else:
        for i, m in enumerate(foes): feet[m] = MONSTERS[Z][i]
    return dict(zoom=Z, feet=feet, mirrored=mirrored)
