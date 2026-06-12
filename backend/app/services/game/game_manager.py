import random
import uuid
import asyncio
from typing import Dict
from .game import Game
from .bot import BotPlayer
from backend.app.core.generators.genarateField import NavalBattleGenerator


class GameManager:
  
  def __init__(self):
    self.active_games = {}
    self.locks: Dict[str, asyncio.Lock] = {}
    self.generator = NavalBattleGenerator()


  def get_lock(self, session_code: str) -> asyncio.Lock:
    """
      Получить или создать блокировку для игровой сессии
    """
    if session_code not in self.locks:
      self.locks[session_code] = asyncio.Lock()
    return self.locks[session_code]


  def create_local_game(self, player1, difficulty):
    bot = BotPlayer(difficulty)
    bot.nickname = "Бот"
    bot.avatar_id = random.randint(0, 9)

    board_data = self.generator.generate(strategy_name="random")

    # преобразуем генерацию в корабли Player
    from .ship import Ship

    bot.board = bot.board  # на всякий случай (можно убрать)

    bot.board.ships = []

    for ship_size, ships in board_data["ships"].items():
      for coords in ships:
        parsed = [
          (int(c[:-1]) - 1, self.generator.cfg.COL_LETTERS.index(c[-1]))
          for c in coords
        ]
        bot.board.ships.append(Ship(int(ship_size), parsed))

    game = Game(player1, bot, mode="local")
    
    # Бот автоматически готов (корабли уже расставлены)
    game.ready_players.add(bot.id)

    session_code = "LOCAL-" + str(uuid.uuid4()).upper()[:6]
    self.active_games[session_code] = game

    return session_code


  def create_online_game(self, player1, session_code):
    game = Game(player1, None, mode="online")
    self.active_games[session_code] = game
    return session_code


  def join_online_game(self, player2, session_code):
    game = self.active_games.get(session_code)
    if game and game.mode == "online" and game.player2 is None:
      game.player2 = player2
      return True
    return False


  def get_game(self, session_code):
    return self.active_games.get(session_code)


  def cleanup_game(self, session_code: str):
    """
      Удалить завершённую игру и её блокировку
    """
    if session_code in self.active_games:
      del self.active_games[session_code]
    if session_code in self.locks:
      del self.locks[session_code]