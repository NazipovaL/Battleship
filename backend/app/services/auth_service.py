from backend.app.database.db import db

class AuthService:

  @staticmethod
  def login(nickname: str, avatar_id: int):
    player_id = db.create_player(nickname, avatar_id)

    if player_id is None:
      return None, "Этот ник и аватар уже заняты"

    return {
      "player_id": player_id
    }, None

  @staticmethod
  def logout(player_id: int):
    return db.delete_player(player_id)