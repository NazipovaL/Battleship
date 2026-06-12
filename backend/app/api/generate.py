from fastapi import APIRouter

from ..core.generators.genarateField import NavalBattleGenerator

router = APIRouter(prefix="/api")
generator = NavalBattleGenerator()

@router.get("/generate-board")
def generate_board(strategy: str = "random"):
  result = generator.generate(strategy_name=strategy)
  return result