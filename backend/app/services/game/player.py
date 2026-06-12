from .board import Board
from typing import List, Optional
class Player:
  
  def __init__(self, player_id: int, nickname: str, avatar_id: int):
    self.id = player_id
    self.nickname = nickname
    self.avatar_id = avatar_id
    self.board = Board()
    self.is_bot = False
    
    
  def setup_board_from_ships(self, ships: List):
    """
      Устанавливает доску списка Pydantic-объектов ShipPlacement
    """
    from .ship import Ship
    self.board = Board()
    self.board.ships = []
    for ship in ships:
      # Принудительно конвертируем списки координат из JSON в кортежи
      coords = [tuple(c) for c in ship.coordinates]
      self.board.ships.append(
          Ship(ship.size, coords)
      )
  
    
  def get_board_state(self, hide_ships: bool = False):
    """
      Возвращает состояние доски для отображения
    """
    if hide_ships:
      # Для поля противника - показываем только выстрелы
      result = [None] * 100
      for shot in self.board.shots:
        idx = shot[0] * 10 + shot[1]
        if shot in self.board.get_hit_cells():
          result[idx] = 'hit'
        else:
          result[idx] = 'miss'
      return result
    else:
      # Для своего поля - показываем всё
      return self.board.to_array()
        
        
  def setup_board_from_generator(self, board_dict):
    """
      Устанавливает доску из генератора (используется для бота)
    """
    from .ship import Ship
    self.board = Board()
    self.board.ships = []
    for ship_size, ships in board_dict["ships"].items():
      for coords in ships:
        parsed = []
        for c in coords:
          row = int(c[:-1]) - 1
          # Временный хак, если _col_to_index отсутствует в классе.
          # Лучше передавать координаты сразу в формате (int, int)
          col = "АБВГДЕЖЗИК".index(c[-1]) # Простой маппинг русских букв
          parsed.append((row, col))
        self.board.ships.append(Ship(int(ship_size), parsed))