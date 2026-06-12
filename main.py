from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI()

# CORS для API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Импортируйте ваш генератор (адаптируйте путь под вашу структуру)
try:
    from backend.app.core.generators.genarateField import NavalBattleGenerator
    generator = NavalBattleGenerator()
    
    @app.get("/api/generate-board")
    def generate_board(strategy: str = "random"):
        result = generator.generate(strategy_name=strategy)
        return result
except ImportError as e:
    @app.get("/api/generate-board")
    def generate_board(strategy: str = "random"):
        return {"error": f"Generator not found: {str(e)}"}

# Раздача статики (фронтенда)
frontend_path = "frontend/public"
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=f"{frontend_path}/src"), name="static")
    app.mount("/assets", StaticFiles(directory=f"{frontend_path}/assets"), name="assets")
    
    @app.get("/")
    async def serve_index():
        return FileResponse(f"{frontend_path}/index.html")
    
    # Для SPA роутинга
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = f"{frontend_path}/{full_path}"
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(f"{frontend_path}/index.html")
