# backend/app/schemas/auth.py
from pydantic import BaseModel
from typing import Optional

class RegisterRequest(BaseModel):
  nickname: str
  avatar_id: int

class RegisterResponse(BaseModel):
  success: bool
  player_id: Optional[int] = None
  session_token: Optional[str] = None
  message: str

class PlayerResponse(BaseModel):
  success: bool
  player_id: Optional[int] = None
  nickname: Optional[str] = None
  avatar_id: Optional[int] = None