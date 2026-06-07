
import json
import os


def save_project(path, state: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def load_project(path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


COMBOS = {
    "Street Brawl":   ["run", "punch", "kick", "dodge", "punch"],
    "Air Combo":      ["jump", "punch", "kick", "uppercut", "land"],
    "Death Sequence": ["run", "jump", "spin", "punch", "death"],
    "Ninja Rush":     ["run", "slide", "kick", "flip", "punch"],
    "Guard Break":    ["guard", "dodge", "uppercut", "kick"],
    "Showoff":        ["idle", "taunt", "spin", "flip", "taunt"],
    "Wall Warrior":   ["run", "walljump", "kick", "land", "punch"],
}
