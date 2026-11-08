#!/usr/bin/env python3
"""Resolve one player's art selection for walking and battle.

Offline art integration helper. This does not add an App selection UI or save
schema. IDs are data keys; neither renderer chooses a different head by weapon.
"""
from dataclasses import dataclass
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
BINDINGS = ROOT / 'Art/Integration/Appearance-battle-custom-heads-v1/scene-bindings.json'


@dataclass(frozen=True)
class Appearance:
    outfit: str
    hair: str
    face: str


class SceneBindings:
    def __init__(self, path=BINDINGS, root=ROOT):
        self.root = Path(root).resolve()
        self.data = json.loads(Path(path).read_text())
        self.players = {}
        for name in ['outfits', 'hair', 'faces']:
            rows = self.data[name]
            if len(rows) != len({r['id'] for r in rows}):
                raise ValueError('duplicate appearance ID')
            setattr(self, name, {r['id']: r for r in rows})

    def file(self, rel):
        path = (self.root / rel).resolve()
        if not path.is_relative_to(self.root) or not path.is_file():
            raise ValueError('missing or unsafe appearance resource: ' + str(rel))
        return path

    def preset(self, name):
        row = self.data['presets'][name]
        return self.validate(Appearance(row['outfit'], row['hair'], row['face']))

    def validate(self, choice):
        if not isinstance(choice, Appearance):
            raise ValueError('complete appearance record required')
        for table, identifier in [(self.outfits, choice.outfit),
                                  (self.hair, choice.hair), (self.faces, choice.face)]:
            if identifier not in table:
                raise ValueError('unknown appearance; no default substitution: ' + str(identifier))
            row = table[identifier]
            manifest = json.loads(self.file(row['locomotionManifest']).read_text())
            if manifest['id'] != identifier:
                raise ValueError('appearance ID differs between scenes')
            if table is self.outfits:
                self.file(row['battleManifest'])
            else:
                for path in row['battleLayers'].values():
                    self.file(path)
        return choice

    def set_player(self, player_id, choice):
        if not isinstance(player_id, str) or not player_id.strip():
            raise ValueError('player ID required')
        # Validate the complete new selection before replacing either scene.
        self.players[player_id] = self.validate(choice)

    def player(self, player_id):
        if player_id not in self.players:
            raise ValueError('player appearance not supplied: ' + str(player_id))
        return self.players[player_id]

    def walking_parts(self, choice):
        self.validate(choice)
        return [self.data['lowerBodyID'], choice.outfit, choice.hair, choice.face]

    def battle(self, choice):
        self.validate(choice)
        layers = {}
        for row in [self.hair[choice.hair], self.faces[choice.face]]:
            for slot, rel in row['battleLayers'].items():
                if slot in layers:
                    raise ValueError('two appearance parts own ' + slot)
                layers[slot] = self.file(rel)
        if set(layers) != {'MeadowBattleHeroHair', 'MeadowBattleHeroFace'}:
            raise ValueError('both battle head layers required; no old head overlay')
        return self.outfits[choice.outfit]['battleItem'], layers
