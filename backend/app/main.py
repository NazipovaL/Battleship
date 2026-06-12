# backend/app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.app.api.routes import auth, game
from backend.app.api import generate # ← добавьте этот импорт
import os

# Пути
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app = FastAPI(title="Морской Бой", description="API для игры Морской бой", version="1.0.0")

# роутеры
app.include_router(auth.router)
app.include_router(game.router)
app.include_router(generate.router)


app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "src/css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "src/js")), name="js")
app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "public/assets")), name="assets")


# Страницы

@app.get("/")
async def serve_index():
  """
    Главная страница - регистрация
  """
  return FileResponse(os.path.join(FRONTEND_DIR, "public/index.html"))

@app.get("/menu")
async def serve_menu():
  """
    Страница меню
  """
  return FileResponse(os.path.join(FRONTEND_DIR, "public/menu.html"))

@app.get("/health")
async def health_check():
  """
    Проверка работоспособности сервера
  """
  return {"status": "alive", "message": "Сервер работает"}

@app.get("/create-game")
async def serve_create_game():
  return FileResponse(os.path.join(FRONTEND_DIR, "public/create-game.html"))

@app.get("/game-mode")
async def serve_game_mode():
  return FileResponse(os.path.join(FRONTEND_DIR, "public/game-mode.html"))

@app.get("/join-game")
async def serve_join_game():
  return FileResponse(os.path.join(FRONTEND_DIR, "public/join-game.html"))

@app.get("/rules")
async def serve_rules():
  return FileResponse(os.path.join(FRONTEND_DIR, "public/rules.html"))

@app.get("/settings")
async def serve_settings():
  return FileResponse(os.path.join(FRONTEND_DIR, "public/settings.html"))

@app.get("/ai-settings")
async def serve_ai_settings():
  return FileResponse(os.path.join(FRONTEND_DIR, "public/ai-settings.html"))

@app.get("/ship-placement")
async def serve_placement():
  return FileResponse(os.path.join(FRONTEND_DIR, "public/ship-placement.html"))

@app.get("/about-authors")
async def serve_authors():
  return FileResponse(os.path.join(FRONTEND_DIR, "public/about-authors.html"))

@app.get("/about-system")
async def serve_system():
  return FileResponse(os.path.join(FRONTEND_DIR, "public/about-system.html"))

@app.get("/game-process")
async def serve_process():
  return FileResponse(os.path.join(FRONTEND_DIR, "public/game-process.html"))

@app.get("/winner")
async def serve_winner():
  return FileResponse(os.path.join(FRONTEND_DIR, "public/winner.html"))