from pydantic import BaseModel
from typing import List, Tuple


class ShipPlacement(BaseModel):
  size: int
  coordinates: List[Tuple[int, int]]


# TODO:внедрить этот класс
class BoardSetupRequest(BaseModel):
  session_code: str
  player_id: int
  ships: List[ShipPlacement]


class ShotActionRequest(BaseModel):
  session_code: str
  player_id: int
  x: int
  y: int