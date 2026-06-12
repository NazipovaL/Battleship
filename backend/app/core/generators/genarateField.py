"""
Naval Battle Ships Generator
Генератор расстановок кораблей для игры "Морской бой" с поддержкой стратегий.
"""

import random
import re
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

@dataclass(frozen=True)
class GameConfig:
  """
    Конфигурация игры
  """
  BOARD_SIZE: int = 10
  SHIPS_CONFIG: Dict[int, int] = field(default_factory=lambda: {4: 1, 3: 2, 2: 3, 1: 4})
  COL_LETTERS: List[str] = field(default_factory=lambda: ['А', 'Б', 'В', 'Г', 'Е', 'Ж', 'З', 'И', 'К', 'Л'])
  ROW_NUMBERS: List[int] = field(default_factory=lambda: list(range(1, 11)))
  MAX_ATTEMPTS: int = 5000
  PLACEMENT_RETRIES: int = 300


# ============================================================================
# МОДЕЛИ ДАННЫХ
# ============================================================================

@dataclass
class ShipPlacement:
  """
    Позиция корабля на доске.
  """
  row: int
  col: int
  size: int
  horizontal: bool
  
  @property
  def cells(self) -> List[Tuple[int, int]]:
    return [(self.row, self.col + i) for i in range(self.size)] if self.horizontal else \
      [(self.row + i, self.col) for i in range(self.size)]


@dataclass
class GenerationResult:
  ships: Dict[int, List[List[str]]]
  board_size: int
  columns: List[str]
  rows: List[int]


# ============================================================================
# АБСТРАКЦИЯ СТРАТЕГИИ
# ============================================================================

class PlacementStrategy(ABC):
  @abstractmethod
  def get_position(self, board, ship_size, board_size, is_valid_pos_func) -> Optional[Tuple[int, int, bool]]:
    """
      Возвращает (row, col, horizontal) для размещения очередного корабля
    """
    pass
  
  @abstractmethod
  def on_generation_start(self, board_size: int) -> None:
    """
      Инициализация стратегии перед началом генерации
    """
    pass


# ============================================================================
# РЕАЛИЗАЦИИ СТРАТЕГИЙ
# ============================================================================

class RandomStrategy(PlacementStrategy):
  
  def get_position(self, board, ship_size, board_size, is_valid_pos_func):
    for _ in range(100):
      horizontal = random.choice([True, False])
      max_col = board_size - ship_size if horizontal else board_size - 1
      max_row = board_size - 1 if horizontal else board_size - ship_size
      row, col = random.randint(0, max_row), random.randint(0, max_col)
      
      if is_valid_pos_func(board, row, col, ship_size, horizontal):
        return row, col, horizontal
      
    return None
  
  
  def on_generation_start(self, board_size: int) -> None: pass


class EdgeStrategy(PlacementStrategy):
  """
    "Береговая" стратегия
  """
  def _get_edge_positions(self, size: int, board_size: int) -> List[Tuple[int, int, bool]]:
    positions = []
    
    for col in range(board_size - size + 1):
      positions.extend([(0, col, True), (board_size - 1, col, True)])
      
    for row in range(board_size - size + 1):
      positions.extend([(row, 0, False), (row, board_size - 1, False)])
      
    return positions


  def get_position(self, board, ship_size, board_size, is_valid_pos_func):
    if ship_size >= 3:
      positions = self._get_edge_positions(ship_size, board_size)
      random.shuffle(positions)
      for r, c, h in positions:
        if is_valid_pos_func(board, r, c, ship_size, h):
          return r, c, h
      return None
    return RandomStrategy().get_position(board, ship_size, board_size, is_valid_pos_func)
  
  
  def on_generation_start(self, board_size: int) -> None: pass


class ClusterStrategy(PlacementStrategy):
  """
    Стратегия «скучкованная»: генерирует расстановку на подполе 8x8, 
    затем случайно сдвигает её в пределах поля 10x10.
    Гарантирует компактность и соблюдение правил за O(N).
  """
  def __init__(self):
    self.queue = []
    self.idx = 0


  def _is_valid_sub(self, board, r, c, size, h):
    sz = len(board)
    
    if h and c + size > sz: 
      return False
    if not h and r + size > sz: 
      return False
    
    # Границы буферной зоны (корабль + 1 клетка)
    r0, r1 = max(0, r-1), min(sz, r + (2 if h else size+1))
    c0, c1 = max(0, c-1), min(sz, c + (size+1 if h else 2))
    
    for rr in range(r0, r1):
      for cc in range(c0, c1):
        is_ship = (h and rr == r and c <= cc < c+size) or \
          (not h and cc == c and r <= rr < r+size)
          
        if not is_ship and board[rr][cc] != 0: 
          return False
        
    return True


  def on_generation_start(self, board_size: int) -> None:
    sub_sz = 8
    board = [[0]*sub_sz for _ in range(sub_sz)]

    ships_order = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]
    self.queue = []

    for size in ships_order:
      placed = False
      for _ in range(2000):
        h = random.choice([True, False])
        r = random.randint(0, sub_sz - 1 if h else sub_sz - size)
        c = random.randint(0, sub_sz - size if h else sub_sz - 1)
        
        if self._is_valid_sub(board, r, c, size, h):
          # Размещение на подполе
          for i in range(size):
            board[r + (0 if h else i)][c + (i if h else 0)] = 1
            
          self.queue.append((r, c, h))
          placed = True
          break
        
      if not placed:
        raise RuntimeError("Кластер: сбой генерации на подполе 8x8")

    # Случайный сдвиг на 0-2 по каждой оси
    off_r = random.randint(0, board_size - sub_sz)
    off_c = random.randint(0, board_size - sub_sz)
    self.queue = [(r+off_r, c+off_c, h) for r, c, h in self.queue]
    self.idx = 0


  def get_position(self, board, ship_size, board_size, is_valid_pos_func):
    if self.idx < len(self.queue):
      pos = self.queue[self.idx]
      self.idx += 1
      return pos
    return None


# ============================================================================
# ГЕНЕРАТОР
# ============================================================================

class NavalBattleGenerator:
  def __init__(self, config: Optional[GameConfig] = None):
    self.cfg = config or GameConfig()
    self._validate_config()

    self.strategies = {
      "random": RandomStrategy(),
      "edge": EdgeStrategy(),
      "cluster": ClusterStrategy(),
    }
  
  
  def _validate_config(self) -> None:
    if len(self.cfg.COL_LETTERS) < self.cfg.BOARD_SIZE:
      raise ValueError("Недостаточно букв для колонок")
    if len(self.cfg.ROW_NUMBERS) < self.cfg.BOARD_SIZE:
      raise ValueError("Недостаточно номеров для строк")
  
  
  def _generate_ships_list(self) -> List[int]:
    return [size for size, count in sorted(self.cfg.SHIPS_CONFIG.items(), reverse=True) for _ in range(count)]
  
  
  def _is_valid_position(self, board, row, col, size, horizontal) -> bool:
    # Границы доски
    if horizontal and col + size > self.cfg.BOARD_SIZE: return False
    if not horizontal and row + size > self.cfg.BOARD_SIZE: return False
    
    # корабль + отступ 1 клетка во все стороны
    if horizontal:
      r_start, r_end = max(0, row - 1), min(self.cfg.BOARD_SIZE, row + 2)
      c_start, c_end = max(0, col - 1), min(self.cfg.BOARD_SIZE, col + size + 1)
    else:
      r_start, r_end = max(0, row - 1), min(self.cfg.BOARD_SIZE, row + size + 1)
      c_start, c_end = max(0, col - 1), min(self.cfg.BOARD_SIZE, col + 2)
    
    # пересечение с другими кораблями
    for r in range(r_start, r_end):
      for c in range(c_start, c_end):
        is_ship = (horizontal and r == row and col <= c < col + size) or \
                  (not horizontal and c == col and row <= r < row + size)
        if not is_ship and board[r][c] != 0:
          return False
    return True
  
  
  def _place_ship_on_board(self, board, placement: ShipPlacement) -> None:
    for r, c in placement.cells:
      board[r][c] = 1
  
  
  def _parse_coord(self, coord: str) -> Tuple[int, int]:
    m = re.match(r'(\d+)([А-Я])', coord)
    if not m: 
      raise ValueError(f"Неверная координата: {coord}")
    return int(m.group(1)) - 1, self.cfg.COL_LETTERS.index(m.group(2))
  
  
  def _extract_ships_from_board(self, board) -> Dict[int, List[List[str]]]:
    ships = {s: [] for s in self.cfg.SHIPS_CONFIG}
    visited = [[False]*self.cfg.BOARD_SIZE for _ in range(self.cfg.BOARD_SIZE)]
    
    
    def dfs(r, c):
      stack, cells = [(r, c)], []
      
      while stack:
        x, y = stack.pop()
        if not (0 <= x < self.cfg.BOARD_SIZE and 0 <= y < self.cfg.BOARD_SIZE): 
          continue
        
        if visited[x][y] or board[x][y] == 0: 
          continue
        
        visited[x][y] = True
        cells.append((x, y))
        
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]: 
          stack.append((x+dx, y+dy))
      return cells
    
    for i in range(self.cfg.BOARD_SIZE):
      for j in range(self.cfg.BOARD_SIZE):
        if board[i][j] == 1 and not visited[i][j]:
          cells = dfs(i, j)
          coords = sorted(f"{self.cfg.ROW_NUMBERS[x]}{self.cfg.COL_LETTERS[y]}" for x, y in cells)
          ships[len(coords)].append(coords)
          
    return {k: v for k, v in ships.items() if v}
  
  
  def _is_straight_ship(self, cells) -> bool:
    rows, cols = [x for x, _ in cells], [y for _, y in cells]
    if len(set(rows)) == 1:
      s = sorted(cols)
      return s == list(range(s[0], s[0] + len(s)))
    if len(set(cols)) == 1:
      s = sorted(rows)
      return s == list(range(s[0], s[0] + len(s)))
    return False
  
  
  def _verify_ship_count(self, board) -> bool:
    found = []
    visited = [[False]*self.cfg.BOARD_SIZE for _ in range(self.cfg.BOARD_SIZE)]
    
    def dfs(r, c):
      stack, cells = [(r, c)], []
      while stack:
        x, y = stack.pop()
        
        if not (0 <= x < self.cfg.BOARD_SIZE and 0 <= y < self.cfg.BOARD_SIZE): 
          continue
        if visited[x][y] or board[x][y] == 0: 
          continue
        
        visited[x][y] = True
        cells.append((x, y))
        
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]: 
          stack.append((x+dx, y+dy))
      return cells
        
    for i in range(self.cfg.BOARD_SIZE):
      for j in range(self.cfg.BOARD_SIZE):
        if board[i][j] == 1 and not visited[i][j]:
          cells = dfs(i, j)
          
          if not self._is_straight_ship(cells): 
            return False
          
          found.append(len(cells))
                
    expected = [s for s, c in self.cfg.SHIPS_CONFIG.items() for _ in range(c)]
    return sorted(found) == sorted(expected)
  
  
  def _try_generate_with_strategy(self, strategy: PlacementStrategy, ships_list: List[int]) -> Optional[Dict]:
    board = [[0] * self.cfg.BOARD_SIZE for _ in range(self.cfg.BOARD_SIZE)]
    strategy.on_generation_start(self.cfg.BOARD_SIZE)
    
    for size in ships_list:
      pos = strategy.get_position(board, size, self.cfg.BOARD_SIZE, self._is_valid_position)
      
      if not pos:
        return None
      
      r, c, h = pos
      self._place_ship_on_board(board, ShipPlacement(r, c, size, h))
            
    if not self._verify_ship_count(board):
      return None
    
    return self._board_to_dict(board)
  
  
  def _board_to_dict(self, board) -> Dict:
    return GenerationResult(
      ships=self._extract_ships_from_board(board),
      board_size=self.cfg.BOARD_SIZE,
      columns=self.cfg.COL_LETTERS.copy(),
      rows=self.cfg.ROW_NUMBERS.copy()
    ).__dict__
  
  
  def generate(self, strategy_name: str = "random") -> Dict:
    if strategy_name not in self.strategies:
      raise ValueError(f"Неизвестная стратегия. Доступны: {list(self.strategies.keys())}")
    
    strategy = self.strategies[strategy_name]
    ships_list = self._generate_ships_list()
    
    for _ in range(self.cfg.MAX_ATTEMPTS):
      result = self._try_generate_with_strategy(strategy, ships_list)
      if result:
        return result
    raise RuntimeError(f"Не удалось сгенерировать расстановку за {self.cfg.MAX_ATTEMPTS} попыток")
  
  
  def print_board(self, board_dict: Dict) -> None:
    size = board_dict["board_size"]
    board = [[0]*size for _ in range(size)]
    for ship_list in board_dict["ships"].values():
      for ship in ship_list:
        for coord in ship:
          r, c = self._parse_coord(coord)
          board[r][c] = 1
    
    print("\n   " + " ".join(board_dict["columns"]))
    print("   " + "─" * (size * 2 + 1))
    for i in range(size):
      label = f"{board_dict['rows'][i]:2}" if board_dict['rows'][i] < 10 else f"{board_dict['rows'][i]}"
      row_str = " ".join("■" if cell else "·" for cell in board[i])
      print(f"{label}| {row_str}")


def main():
  generator = NavalBattleGenerator()
  strategies = ["random", "edge", "cluster"]
  
  print("\n" + "═" * 60)
  print("ГЕНЕРАТОР РАССТАНОВОК «МОРСКОЙ БОЙ»")
  print("═" * 60)
  
  for strat in strategies:
    print(f"\n{'─' * 60}")
    print(f"Стратегия: {strat.upper()}")
    print(f"{'─' * 60}")
    
    try:
      result = generator.generate(strategy_name=strat)
      generator.print_board(result)
    except Exception as e:
      print(f"✗ Ошибка: {e}")
      
  print(f"\n{'═' * 60}\n")

if __name__ == "__main__":
  main()