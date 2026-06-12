from typing import Dict, Optional
from backend.app.services.game.player import Player

class Database:
  def __init__(self):
    self.active_players: Dict[int, dict] = {}
    self._next_player_id = 1


  def create_player(self, nickname: str, avatar_id: int) -> Optional[int]:
    # проверка уникальности пары
    for player in self.active_players.values():
      if (
        player["nickname"].lower() == nickname.lower() and
        player["avatar_id"] == avatar_id
      ):
        return None

    player_id = self._next_player_id
    self._next_player_id += 1

    self.active_players[player_id] = {
      "id": player_id,
      "nickname": nickname,
      "avatar_id": avatar_id
    }

    return player_id


  def delete_player(self, player_id: int) -> bool:
    return self.active_players.pop(player_id, None) is not None


  def get_player(self, player_id: int) -> Optional[dict]:
    return self.active_players.get(player_id)
    
    
  def get_player_object(self, player_id: int) -> Optional[Player]:
    """Возвращает игрока как объект Player, а не dict."""
    data = self.active_players.get(player_id)
    if not data:
        return None
    return Player(
        player_id=data["id"],
        nickname=data["nickname"],
        avatar_id=data["avatar_id"]
    )    
      
db = Database()