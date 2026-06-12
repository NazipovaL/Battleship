from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.generators.genarateField import NavalBattleGenerator

app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

generator = NavalBattleGenerator()

# @app.get("/api/generate-board")
@app.get("/api/generate-board")
def generate_board(strategy: str = "random"):
  result = generator.generate(strategy_name=strategy)
  return result