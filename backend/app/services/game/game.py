from .player import Player
from .board import ShotResult

from pydantic import BaseModel
from typing import List, Tuple


class ShotActionRequest(BaseModel):
  session_code: str
  player_id: int
  x: int
  y: int

class Game:
  
  def __init__(self, player1: Player, player2: Player, mode: str):
    self.player1 = player1
    self.player2 = player2
    self.mode = mode  # local / online
    self.current_player = player1
    self.winner = None
    self.ready_players = set()
    self.is_finished = False  # Флаг завершения игры (защита от двойного cleanup)


  def get_enemy(self):
    return self.player2 if self.current_player == self.player1 else self.player1


  def make_move(self, coord):
    enemy = self.get_enemy()
    result = enemy.board.receive_shot(coord)

    if self.current_player.is_bot:
      self.current_player.on_shot_result(coord, result, enemy.board)

    if result == ShotResult.MISS:
      self.current_player = enemy

    if enemy.board.all_ships_sunk():
      self.winner = self.current_player

    return result
  
  
  def get_enemy_board(self):
    enemy = self.get_enemy()
    return enemy.board