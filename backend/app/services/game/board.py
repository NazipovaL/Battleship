from .ship import Ship
from enum import Enum
from typing import List, Optional, Tuple


class ShotResult(Enum):
  MISS = "miss"
  HIT = "hit"
  KILL = "kill"
  
  
class Board:
  def __init__(self):
    self.ships: list[Ship] = []
    self.shots = set()
  
  
  def mark_surroundings_as_shot(self, ship: Ship):
    """Автоматически проставляет промахи вокруг уничтоженного корабля."""
    for r, c in ship.coordinates:
      for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
          nr, nc = r + dr, c + dc
          # Проверяем границы поля 10x10
          if 0 <= nr < 10 and 0 <= nc < 10:
            coord = (nr, nc)
            # Не ставим промах на сам корабль
            if coord not in ship.coordinates:
              self.shots.add(coord)
  
  
  def receive_shot(self, coord):
    if coord in self.shots:
        raise ValueError("Клетка уже обстреляна")
    self.shots.add(coord)
    for ship in self.ships:
        if coord in ship.coordinates:
            ship.hit(coord)
            if ship.is_sunk():
                self.mark_surroundings_as_shot(ship)
                return ShotResult.KILL
            return ShotResult.HIT
    return ShotResult.MISS
 
 
  def all_ships_sunk(self):
    return all(ship.is_sunk() for ship in self.ships)
  
  def get_hit_cells(self) -> List[Tuple[int, int]]:
      hits = []
      for ship in self.ships:
          hits.extend(ship.hits)
      return hits
  
  
  def is_cell_shot(self, coord: Tuple[int, int]) -> bool:
    return coord in self.shots
    
    
  def to_array(self) -> List[Optional[str]]:
    result = [None] * 100
    for ship in self.ships:
      for coord in ship.coordinates:
        idx = coord[0] * 10 + coord[1]
        if coord in ship.hits:
          result[idx] = 'hit'
        else:
          result[idx] = 'ship'
    for shot in self.shots:
      if shot not in self.get_hit_cells():
        idx = shot[0] * 10 + shot[1]
        result[idx] = 'miss'
    return result
    
    
  def get_cell_state(self, x: int, y: int) -> Optional[str]:
    coord = (x, y)
    for ship in self.ships:
      if coord in ship.coordinates:
        return 'hit' if coord in ship.hits else 'ship'
    if coord in self.shots:
      return 'miss'
    return None