# models/player.py
from dataclasses import dataclass

@dataclass
class Player:
    game_name: str
    tag_line: str