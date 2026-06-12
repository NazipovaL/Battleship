from typing import Dict, Optional
from fastapi import WebSocket


class ConnectionManager:
  
  def __init__(self):
    # session_code -> {player_id: websocket}
    self.active_connections: Dict[str, Dict[int, WebSocket]] = {}

  async def connect(self, websocket: WebSocket, session_code: str, player_id: int):
    await websocket.accept()
    if session_code not in self.active_connections:
      self.active_connections[session_code] = {}
    self.active_connections[session_code][player_id] = websocket


  def disconnect(self, session_code: str, player_id: int):
    if session_code in self.active_connections:
      if player_id in self.active_connections[session_code]:
        del self.active_connections[session_code][player_id]
      if not self.active_connections[session_code]:
        del self.active_connections[session_code]


  async def send_to_player(self, session_code: str, player_id: int, message: dict):
    """
      Отправить сообщение конкретному игроку
    """
    if session_code in self.active_connections:
      if player_id in self.active_connections[session_code]:
        try:
          await self.active_connections[session_code][player_id].send_json(message)
        except:
          pass


  async def broadcast(self, session_code: str, message: dict, exclude_player_id: int = None):
    """
      Отправить сообщение всем подключенным клиентам в сессии
    """
    if session_code in self.active_connections:
      for player_id, connection in self.active_connections[session_code].items():
        if exclude_player_id and player_id == exclude_player_id:
          continue
        try:
          await connection.send_json(message)
        except:
          pass


  def is_player_connected(self, session_code: str, player_id: int) -> bool:
    """
      Проверить, подключен ли игрок
    """
    if session_code in self.active_connections:
      return player_id in self.active_connections[session_code]
    return False


manager = ConnectionManager()