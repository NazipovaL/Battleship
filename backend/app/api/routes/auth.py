from fastapi import APIRouter
from backend.app.schemas.auth import RegisterRequest, RegisterResponse, PlayerResponse
from backend.app.services.auth_service import AuthService    
from fastapi import Query

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login", response_model=RegisterResponse)
async def login(data: RegisterRequest):
  result, error = AuthService.login(data.nickname, data.avatar_id)

  if error:
    return RegisterResponse(success=False, message=error)

  return RegisterResponse(
    success=True,
    player_id=result["player_id"],
    message=""
  )


@router.post("/logout")
async def logout(player_id: int = Query(...)):
  success = AuthService.logout(player_id)

  if success:
    return {"success": True}

  return {"success": False, "message": "Игрок не найден"}
  

