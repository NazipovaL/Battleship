import asyncio
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query
from backend.app.services.game.connection_manager import manager
from backend.app.services.game.game_manager import GameManager
from backend.app.schemas.game import BoardSetupRequest, ShotActionRequest
from backend.app.database.db import db
from backend.app.services.game.board import ShotResult
from pydantic import BaseModel
from typing import List, Optional


router = APIRouter(prefix="/api/game", tags=["game"])
game_manager = GameManager()


async def handle_move_logic(session_code: str, player_id: int, x: int, y: int):
  """
    Общая логика обработки хода для REST и WebSocket
  """
  async with game_manager.get_lock(session_code):
      game = game_manager.get_game(session_code)
      
      if not game:
        return None, "Игра не найдена"
      if game.is_finished:
        return None, "Игра уже завершена"
      if game.current_player.id != player_id:
        return None, "Не ваш ход"
      
      coord = (x, y)
      try:
        result = game.make_move(coord)
      except ValueError as e:
        return None, str(e)
      
      move_data = {
        "player_id": player_id,
        "x": x,
        "y": y,
        "result": result.value,
        "game_over": game.winner is not None,
        "current_turn": game.current_player.id
      }
      
      # Отправить подтверждение конкретному игроку
      await manager.send_to_player(session_code, player_id, {
        "type": "move_confirmed",
        "data": move_data
      })
      
      # Отправить событие move_made всем
      await manager.broadcast(session_code, {
        "type": "move_made",
        "data": move_data
      })
      
      # Если игра окончена - отправить game_over и очистить
      if game.winner is not None:
        game.is_finished = True
        await manager.broadcast(session_code, {
          "type": "game_over",
          "data": {
            "winner_id": game.winner.id,
            "winner_nickname": game.winner.nickname
          }
        })
        asyncio.create_task(_delayed_cleanup(session_code, delay=5.0))
        return {
          "success": True,
          "result": result.value,
          "game_over": True
        }, None
      
      # Если следующий ход бота - выполнить ходы бота автоматически
      if game.current_player.is_bot:
        await _execute_bot_moves(session_code)
      
      return {
        "success": True,
        "result": result.value,
        "game_over": False
      }, None


async def _execute_bot_moves(session_code: str):
  """Выполняет ходы бота, пока он попадает или игра не окончена"""
  lock = game_manager.get_lock(session_code)
  already_locked = lock.locked()
  
  # Если lock уже захвачен (вызов из handle_move_logic), не захватываем снова
  if not already_locked:
    await lock.acquire()
  
  try:
    game = game_manager.get_game(session_code)
    if not game or game.is_finished:
      return
    
    while game and not game.winner and game.current_player.is_bot and not game.is_finished:
      bot = game.current_player
      enemy_board = game.get_enemy_board()
      
      try:
        coord = bot.make_move(enemy_board)
      except Exception:
        # Бот не может сделать ход (все клетки обстреляны или ошибка стратегии)
        break
      
      # Защита от невалидных координат
      if not coord or not isinstance(coord, tuple) or len(coord) != 2:
        break
      
      x, y = coord
      
      try:
        result = game.make_move(coord)
      except ValueError:
        # Невалидный ход - выход
        break
      
      if result is None:
        break
      
      # Отправить событие move_made для хода бота
      move_data = {
        "player_id": bot.id,
        "x": x,
        "y": y,
        "result": result.value,
        "game_over": game.winner is not None,
        "current_turn": game.current_player.id
      }
      
      await manager.broadcast(session_code, {
        "type": "move_made",
        "data": move_data
      })
      
      # Если игра окончена - отправить game_over и очистить
      if game.winner is not None:
        game.is_finished = True
        await manager.broadcast(session_code, {
          "type": "game_over",
          "data": {
            "winner_id": game.winner.id,
            "winner_nickname": game.winner.nickname
          }
        })
        asyncio.create_task(_delayed_cleanup(session_code, delay=5.0))
        break
      
      # Если промах - ход переходит к другому игроку, выход из цикла
      if result == ShotResult.MISS:
        break
  finally:
    if not already_locked:
      lock.release()


async def _delayed_cleanup(session_code: str, delay: float = 5.0):
  """
    Отложенная очистка игры после завершения
  """
  await asyncio.sleep(delay)
  game = game_manager.get_game(session_code)
  if game and game.is_finished:
      game_manager.cleanup_game(session_code)


class CreateLocalRequest(BaseModel):
  player_id: int
  difficulty: str
    
    
@router.post("/create/local")
def create_local(req: CreateLocalRequest):
  player = db.get_player_object(req.player_id)
  if not player:
    raise HTTPException(status_code=404, detail="Игрок не найден")
  
  session_code = game_manager.create_local_game(player, req.difficulty)
  return {"success": True, "session_code": session_code}


class CreateOnlineRequest(BaseModel):
  player_id: int
  session_code: str
    
    
@router.post("/create/online")
def create_online(req: CreateOnlineRequest):
  player = db.get_player_object(req.player_id)
  if not player:
    raise HTTPException(status_code=404, detail="Игрок не найден")
  
  game_manager.create_online_game(player, req.session_code)
  return {"success": True, "session_code": req.session_code}


class JoinOnlineRequest(BaseModel):
  player_id: int
  session_code: str
    
    
@router.post("/join")
async def join_online(req: JoinOnlineRequest):
  player = db.get_player_object(req.player_id)
  if not player:
    raise HTTPException(status_code=404, detail="Игрок не найден")
  
  success = game_manager.join_online_game(player, req.session_code)
  if not success:
    return {
      "success": False,
      "message": "Сессия не найдена или уже заполнена"
    }
  
  # Отправить событие через WebSocket
  await manager.broadcast(req.session_code, {
    "type": "player_joined",
    "data": {
      "player_id": player.id,
      "nickname": player.nickname
    }
  })
  
  return {"success": True}
  
  
@router.post("/setup")
async def setup_board(req: BoardSetupRequest):
  game = game_manager.get_game(req.session_code)

  if not game:
    raise HTTPException(status_code=404, detail="Игра не найдена")

  if game.player1.id == req.player_id:
    player = game.player1
  elif game.player2 and game.player2.id == req.player_id:
    player = game.player2
  else:
    raise HTTPException(status_code=400, detail="Игрок не найден в игре")

  game.ready_players.add(player.id)
  player.setup_board_from_ships(req.ships)

  # Отправить событие player_ready
  await manager.broadcast(req.session_code, {
    "type": "player_ready",
    "data": {
      "player_id": player.id,
      "ready_count": len(game.ready_players)
    }
  })

  # Если оба готовы - отправить game_start
  if len(game.ready_players) == 2:
    await manager.broadcast(req.session_code, {
      "type": "game_start",
      "data": {
        "message": "Игра началась!"
      }
    })

  return {"success": True}
  
  
@router.post("/shoot")
async def make_shot(req: ShotActionRequest):
  result, error = await handle_move_logic(req.session_code, req.player_id, req.x, req.y)
  if error:
    raise HTTPException(status_code=400, detail=error)
  return result


class PlayerInfo(BaseModel):
  id: int
  nickname: str
  avatar_id: int


class GameStateResponse(BaseModel):
  success: bool
  player_board: Optional[List] = None
  enemy_board: Optional[List] = None
  is_player_turn: bool = True
  game_over: bool = False
  winner: Optional[str] = None
  player: Optional[PlayerInfo] = None
  enemy: Optional[PlayerInfo] = None
    
    
class GiveUpRequest(BaseModel):
  session_code: str
  player_id: int
    

@router.get("/state/{session_code}/{player_id}", response_model=GameStateResponse)
def get_game_state(session_code: str, player_id: int):
  game = game_manager.get_game(session_code)
  if not game:
    raise HTTPException(status_code=404, detail="Игра не найдена")
  
  # Определить, какой игрок запрашивает состояние
  if game.player1 and game.player1.id == player_id:
    current_player = game.player1
    enemy_player = game.player2
  elif game.player2 and game.player2.id == player_id:
    current_player = game.player2
    enemy_player = game.player1
  else:
    raise HTTPException(status_code=400, detail="Игрок не найден в игре")
  
  player_board = current_player.board.to_array() if current_player else None
  enemy_board = enemy_player.get_board_state(hide_ships=True) if enemy_player else None
  
  
  player_info = PlayerInfo(
    id=current_player.id,
    nickname=current_player.nickname,
    avatar_id=current_player.avatar_id
  ) if current_player else None

  enemy_info = PlayerInfo(
    id=enemy_player.id,
    nickname=enemy_player.nickname,
    avatar_id=enemy_player.avatar_id
  ) if enemy_player else None
  
  
  return GameStateResponse(
    success=True,
    player_board=player_board,
    enemy_board=enemy_board,
    is_player_turn=game.current_player == current_player,
    game_over=game.winner is not None,
    winner=game.winner.nickname if game.winner else None,
    player=player_info,
    enemy=enemy_info 
  )
    
    
@router.post("/give-up")
async def give_up(req: GiveUpRequest):
  async with game_manager.get_lock(req.session_code):
    game = game_manager.get_game(req.session_code)
    if not game:
      raise HTTPException(status_code=404, detail="Игра не найдена")
    
    if game.is_finished:
      return {"success": True}
    
    if game.player1 and game.player1.id == req.player_id:
      game.winner = game.player2
    elif game.player2 and game.player2.id == req.player_id:
      game.winner = game.player1
    else:
      raise HTTPException(status_code=400, detail="Игрок не участвует в этой сессии")
    
    game.is_finished = True
    
    await manager.broadcast(req.session_code, {
      "type": "game_over",
      "data": {
        "winner_id": game.winner.id,
        "winner_nickname": game.winner.nickname
      }
    })
    
    asyncio.create_task(_delayed_cleanup(req.session_code, delay=5.0))
  
  return {"success": True}

  
@router.get("/ready/{session_code}")
def check_ready(session_code: str):
  game = game_manager.get_game(session_code)

  if not game:
    raise HTTPException(status_code=404, detail="Игра не найдена")

  return {"ready": len(game.ready_players) == 2}


@router.websocket("/ws/{session_code}")
async def websocket_endpoint(
  websocket: WebSocket,
  session_code: str,
  player_id: int = Query(...)
):
  await manager.connect(websocket, session_code, player_id)
  
  game = game_manager.get_game(session_code)
  
  # Отправить текущее состояние игры при подключении
  if game:
    # Определить, какой игрок подключился
    if game.player1 and game.player1.id == player_id:
      current_player = game.player1
      enemy_player = game.player2
    elif game.player2 and game.player2.id == player_id:
      current_player = game.player2
      enemy_player = game.player1
    else:
      current_player = None
      enemy_player = None
  
    player_board = current_player.board.to_array() if current_player else None
    enemy_board = enemy_player.get_board_state(hide_ships=True) if enemy_player else None
    
    await manager.send_to_player(session_code, player_id, {
      "type": "init_state",
      "data": {
        "player_board": player_board,
        "enemy_board": enemy_board,
        "is_player_turn": game.current_player == current_player if current_player else False,
        "game_over": game.winner is not None,
        "winner": game.winner.nickname if game.winner else None,
        "ready_count": len(game.ready_players),
        "player": {
          "id": current_player.id,
          "nickname": current_player.nickname,
          "avatar_id": current_player.avatar_id
        } if current_player else None,

        "enemy": {
          "id": enemy_player.id,
          "nickname": enemy_player.nickname,
          "avatar_id": enemy_player.avatar_id
        } if enemy_player else None,
      }
    })
  
  try:
    while True:
      data = await websocket.receive_json()
      msg_type = data.get("type")
      msg_data = data.get("data", {})
      
      if msg_type == "move":
        # Обработка хода через WebSocket
        x = msg_data.get("x")
        y = msg_data.get("y")
        
        if x is None or y is None:
          await manager.send_to_player(session_code, player_id, {
            "type": "error",
            "data": {"message": "Неверные координаты"}
          })
          continue
        
        result, error = await handle_move_logic(session_code, player_id, x, y)
        
        if error:
          await manager.send_to_player(session_code, player_id, {
            "type": "error",
            "data": {"message": error}
          })
        # Подтверждение уже отправлено внутри handle_move_logic
  
  except WebSocketDisconnect:
    manager.disconnect(session_code, player_id)
    
    # Обработка отключения игрока
    async with game_manager.get_lock(session_code):
      game = game_manager.get_game(session_code)
      
      if game and not game.is_finished and game.winner is None:
        # Назначить победителем второго игрока
        if game.player1 and game.player1.id == player_id:
          game.winner = game.player2
        elif game.player2 and game.player2.id == player_id:
          game.winner = game.player1
        
        if game.winner:
          game.is_finished = True
          
          await manager.broadcast(session_code, {
            "type": "game_over",
            "data": {
              "winner_id": game.winner.id,
              "winner_nickname": game.winner.nickname
            }
          })
          
          asyncio.create_task(_delayed_cleanup(session_code, delay=5.0))
    
    # Уведомить другого игрока об отключении
    await manager.broadcast(session_code, {
      "type": "player_disconnected",
      "data": {
        "player_id": player_id
      }
    })