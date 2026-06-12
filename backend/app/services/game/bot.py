"""
Бот для игры «Морской бой» с тремя уровнями сложности.
"""

import random
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Set, Tuple, Optional, Dict

from .player import Player
from .board import Board, ShotResult


# ============================================================================
# КОНСТАНТЫ И ВСПОМОГАТЕЛЬНЫЕ ТИПЫ
# ============================================================================

BOARD_SIZE = 10
DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Up, Down, Left, Right
ALL_NEIGHBORS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


@dataclass
class HuntState:
    """Состояние режима «добивание» для крестообразного метода."""
    first_hit: Tuple[int, int]
    direction: Optional[Tuple[int, int]] = None  # Найденное направление
    last_pos: Optional[Tuple[int, int]] = None   # Последняя успешная позиция
    tried_directions: List[Tuple[int, int]] = field(default_factory=list)


@dataclass
class CellScore:
    """Оценка клетки для признаковой стратегии."""
    coord: Tuple[int, int]
    score: float
    reasons: List[str] = field(default_factory=list)  # Для отладки


# ============================================================================
# АБСТРАКЦИЯ СТРАТЕГИИ
# ============================================================================

class BotStrategy(ABC):
    """Базовый класс стратегии бота."""
    
    def __init__(self):
        self.hunt_stack: List[HuntState] = []  # Стек для множественных раненых кораблей
        self.shot_history: Set[Tuple[int, int]] = set()
    
    @abstractmethod
    def get_move(self, board: Board) -> Tuple[int, int]:
        """Возвращает координаты следующего выстрела."""
        pass
    
    def _is_valid(self, board: Board, coord: Tuple[int, int]) -> bool:
        """Проверяет, можно ли стрелять в клетку."""
        r, c = coord
        return (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and 
                coord not in board.shots and coord not in self.shot_history)
    
    def _get_unshot_neighbors(self, board: Board, coord: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Возвращает необстрелянных соседей клетки (по кресту)."""
        r, c = coord
        neighbors = []
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if self._is_valid(board, (nr, nc)):
                neighbors.append((nr, nc))
        return neighbors
    
    def _mark_shot(self, coord: Tuple[int, int]):
        """Отмечает клетку как обстрелянную во внутренней истории."""
        self.shot_history.add(coord)
    
    def _start_hunt(self, coord: Tuple[int, int]):
        """Начинает режим добивания с указанной клетки."""
        self.hunt_stack.append(HuntState(first_hit=coord))
    
    def _continue_hunt_cross(self, board: Board, state: HuntState) -> Optional[Tuple[int, int]]:
        """
        Крестообразный метод добивания.
        Стреляет поочерёдно вверх/вниз/влево/вправо от первого попадания,
        затем продолжает в найденном направлении.
        """
        # Если направление уже найдено — продолжаем линейно
        if state.direction:
            dr, dc = state.direction
            next_pos = (state.last_pos[0] + dr, state.last_pos[1] + dc) if state.last_pos else None
            if next_pos and self._is_valid(board, next_pos):
                return next_pos
            # Если уперлись в край или уже стреляли — завершаем этот корабль
            return None
        
        # Ищем направление: перебираем 4 стороны от first_hit
        for dr, dc in DIRECTIONS:
            if (dr, dc) in state.tried_directions:
                continue
            neighbor = (state.first_hit[0] + dr, state.first_hit[1] + dc)
            if self._is_valid(board, neighbor):
                state.tried_directions.append((dr, dc))
                return neighbor
        
        # Все направления проверены, но второе попадание не найдено (корабль 1×1)
        return None
    
    def _continue_hunt_adaptive(self, board: Board, state: HuntState) -> Optional[Tuple[int, int]]:
        """
        Адаптивный метод добивания (для сложного уровня).
        Анализирует контекст: соседние попадания, вероятные направления,
        оставшиеся размеры кораблей.
        """
        # Собираем все клетки раненого корабля
        ship_cells = [state.first_hit]
        if state.last_pos and state.last_pos != state.first_hit:
            ship_cells.append(state.last_pos)
        
        # Кандидаты: все необстрелянные соседи по кресту от известных клеток
        candidates = []
        for cell in ship_cells:
            for dr, dc in DIRECTIONS:
                neighbor = (cell[0] + dr, cell[1] + dc)
                if self._is_valid(board, neighbor):
                    # Оценка приоритета
                    score = 1.0
                    # Приоритет: продолжение линии, если уже есть направление
                    if state.direction:
                        expected = (cell[0] + state.direction[0], cell[1] + state.direction[1])
                        if neighbor == expected:
                            score *= 3.0
                    # Приоритет: клетки с большим числом необстрелянных соседей (больше информации)
                    unshot_around = sum(1 for d in DIRECTIONS 
                                       if self._is_valid(board, (neighbor[0]+d[0], neighbor[1]+d[1])))
                    score *= (1 + unshot_around * 0.2)
                    
                    candidates.append(CellScore(coord=neighbor, score=score))
        
        if not candidates:
            return None
        
        # Выбираем клетку с максимальным скором + небольшой рандом для вариативности
        candidates.sort(key=lambda x: x.score, reverse=True)
        top = [c for c in candidates if abs(c.score - candidates[0].score) < 0.1]
        return random.choice(top).coord
    
    def handle_shot_result(self, board: Board, coord: Tuple[int, int], result: ShotResult):
        """
        Обновляет внутреннее состояние стратегии после выстрела.
        Должен вызываться из Game после receive_shot.
        """
        self._mark_shot(coord)
        
        if result == ShotResult.HIT:
            # Начинаем или продолжаем добивание
            if not any(s.first_hit == coord for s in self.hunt_stack):
                self._start_hunt(coord)
        elif result == ShotResult.KILL:
            # Корабль уничтожен — убираем из стека и блокируем соседние клетки
            for i, state in enumerate(self.hunt_stack):
                if state.first_hit == coord or state.last_pos == coord:
                    self.hunt_stack.pop(i)
                    break
            # Блокируем окружение убитого корабля (правило: корабли не касаются)
            self._block_around_ship(board, coord)
    
    def _block_around_ship(self, board: Board, coord: Tuple[int, int]):
        """Отмечает все клетки вокруг убитого корабля как «недоступные для стратегии»."""
        # В реальной игре это делает Board, но для стратегии полезно знать
        r, c = coord
        for dr in [-1, 0,  1]:
            for dc in [-1, 0, 1]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                    self.shot_history.add((nr, nc))  # Не стрелять сюда


# ============================================================================
# ЛЕГКИЙ УРОВЕНЬ: CheckerboardStrategy
# ============================================================================

class CheckerboardStrategy(BotStrategy):
    """
    Стратегия «шахматный порядок».
    Обстреливает клетки одного цвета ((r + c) % 2 == const),
    что гарантирует нахождение любого корабля за минимальное число ходов.
    """
    
    def __init__(self):
        super().__init__()
        self.pattern_parity = random.choice([0, 1])  # Случайный цвет для вариативности
        self.scan_queue = self._generate_scan_order()
    
    def _generate_scan_order(self) -> List[Tuple[int, int]]:
        """Генерирует очередь клеток в шахматном порядке."""
        cells = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)
                 if (r + c) % 2 == self.pattern_parity]
        random.shuffle(cells)  # Рандом внутри паттерна для непредсказуемости
        return cells
    
    def get_move(self, board: Board) -> Tuple[int, int]:
        # 1. Приоритет: добивание раненого корабля (крестообразный метод)
        if self.hunt_stack:
            state = self.hunt_stack[-1]
            move = self._continue_hunt_cross(board, state)
            if move and self._is_valid(board, move):
                return move
            # Если не удалось продолжить — убираем завершённый hunt
            if self.hunt_stack:
                self.hunt_stack.pop()
        
        # 2. Сканирование по шахматному паттерну
        while self.scan_queue:
            candidate = self.scan_queue.pop(0)
            if self._is_valid(board, candidate):
                return candidate
        
        # 3. Фолбэк: любые необстрелянные клетки
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self._is_valid(board, (r, c)):
                    return (r, c)
        
        # Теоретически недостижимо
        return (0, 0)


# ============================================================================
# СРЕДНИЙ УРОВЕНЬ: DiagonalStrategy
# ============================================================================

class DiagonalStrategy(BotStrategy):
    """
    Диагональная стратегия.
    Обстрел ведётся вдоль диагоналей поля (r - c = const или r + c = const).
    Порядок обхода диагоналей: от центра к краям для быстрого покрытия.
    """
    
    def __init__(self):
        super().__init__()
        self.diagonal_queue = self._generate_diagonal_order()
    
    def _generate_diagonal_order(self) -> List[Tuple[int, int]]:
        """Генерирует очередь клеток по диагоналям от центра."""
        # Используем сумму координат (r + c) как индекс диагонали
        diagonals: Dict[int, List[Tuple[int, int]]] = {}
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                diag_id = r + c
                diagonals.setdefault(diag_id, []).append((r, c))
        
        # Порядок: сначала диагонали ближе к центру (сумма ~9), потом к краям
        center = BOARD_SIZE - 1
        sorted_diags = sorted(diagonals.keys(), key=lambda d: abs(d - center))
        
        result = []
        for diag_id in sorted_diags:
            cells = diagonals[diag_id]
            random.shuffle(cells)  # Рандом внутри диагонали
            result.extend(cells)
        return result
    
    def get_move(self, board: Board) -> Tuple[int, int]:
        # 1. Приоритет: добивание (крестообразный метод)
        if self.hunt_stack:
            state = self.hunt_stack[-1]
            move = self._continue_hunt_cross(board, state)
            if move and self._is_valid(board, move):
                return move
            if self.hunt_stack:
                self.hunt_stack.pop()
        
        # 2. Сканирование по диагоналям
        while self.diagonal_queue:
            candidate = self.diagonal_queue.pop(0)
            if self._is_valid(board, candidate):
                return candidate
        
        # 3. Фолбэк
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self._is_valid(board, (r, c)):
                    return (r, c)
        return (0, 0)


# ============================================================================
# СЛОЖНЫЙ УРОВЕНЬ: FeatureBasedStrategy
# ============================================================================

class FeatureBasedStrategy(BotStrategy):
  """
    Признаковая стратегия (Feature-Based).
    Оценивает каждую клетку по взвешенной комбинации признаков:
    - вероятность наличия корабля (на основе оставшихся размеров)
    - количество соседних необстрелянных клеток (информативность)
    - близость к предыдущим попаданиям
    - принадлежность к «горячим» зонам
    
    Для добивания использует адаптивный метод.
  """
  
  # Веса признаков (можно настраивать)
  WEIGHTS = {
    'ship_probability': 4.0,
    'information_gain': 1.5,
    'proximity_to_hit': 2.0,
    'edge_penalty': -0.5,
  }
  
  
  def __init__(self):
    super().__init__()
    self.remaining_ships = {4: 1, 3: 2, 2: 3, 1: 4}  # Статическая конфигурация
    self.hit_clusters: List[List[Tuple[int, int]]] = []  # Группы связанных попаданий
  
  
  def _calculate_ship_probability(self, board: Board, coord: Tuple[int, int]) -> float:
    """
      Оценивает вероятность, что в клетке есть корабль,
      на основе оставшихся размеров и геометрии.
    """
    r, c = coord
    score = 0.0
    
    for size in self.remaining_ships:
      if self.remaining_ships[size] <= 0:
        continue
      # Проверяем, может ли корабль такого размера поместиться здесь
      for dr, dc in [(0, 1), (1, 0)]:  # горизонтально и вертикально
        can_place = True
        for i in range(size):
          nr, nc = r + i*dr, c + i*dc
          if not (0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE):
            can_place = False
            break
          # Если клетка уже обстреляна и там промах — корабль не может быть
          if (nr, nc) in board.shots and (nr, nc) not in [h for cluster in self.hit_clusters for h in cluster]:
            can_place = False
            break
        if can_place:
          score += 1.0 / size  # Меньшие корабли более вероятны
    
    return score
  
  
  def _calculate_information_gain(self, board: Board, coord: Tuple[int, int]) -> float:
    """
      Оценивает, сколько новой информации даст выстрел в эту клетку
      (число соседних необстрелянных клеток).
    """
    r, c = coord
    gain = 0
    for dr in [-1, 0, 1]:
      for dc in [-1, 0, 1]:
        if dr == 0 and dc == 0:
          continue
        nr, nc = r + dr, c + dc
        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
          if (nr, nc) not in board.shots and (nr, nc) not in self.shot_history:
            gain += 1
    return gain
  
  
  def _calculate_proximity_to_hit(self, board: Board, coord: Tuple[int, int]) -> float:
    """
      Даёт бонус клеткам, близким к уже обстрелянным попаданиям
      (вероятность продолжения корабля).
    """
    r, c = coord
    min_dist = float('inf')
    for cluster in self.hit_clusters:
      for hr, hc in cluster:
        dist = abs(r - hr) + abs(c - hc)  # Манхэттенское расстояние
        if dist < min_dist:
          min_dist = dist
    return 1.0 / (min_dist + 1) if min_dist != float('inf') else 0.0
  
  
  def _calculate_edge_penalty(self, coord: Tuple[int, int]) -> float:
      """
      Небольшой штраф для краевых клеток (статистически там реже размещают).
      """
      r, c = coord
      dist_to_edge = min(r, c, BOARD_SIZE-1-r, BOARD_SIZE-1-c)
      return 0 if dist_to_edge >= 2 else -0.5 * (2 - dist_to_edge)
  
  
  def _score_cell(self, board: Board, coord: Tuple[int, int]) -> CellScore:
    """
      Вычисляет итоговую оценку клетки.
    """
    score = 0.0
    reasons = []
    
    # Признак 1: вероятность корабля
    p_ship = self._calculate_ship_probability(board, coord)
    score += self.WEIGHTS['ship_probability'] * p_ship
    if p_ship > 0:
      reasons.append(f"ship_prob={p_ship:.2f}")
    
    # Признак 2: информативность
    info = self._calculate_information_gain(board, coord)
    score += self.WEIGHTS['information_gain'] * info
    if info > 0:
      reasons.append(f"info_gain={info}")
    
    # Признак 3: близость к попаданиям
    prox = self._calculate_proximity_to_hit(board, coord)
    score += self.WEIGHTS['proximity_to_hit'] * prox
    if prox > 0.3:
      reasons.append(f"proximity={prox:.2f}")
    
    # Признак 4: штраф за края
    edge = self._calculate_edge_penalty(coord)
    score += edge
    if edge < 0:
      reasons.append(f"edge_penalty={edge}")
    
    return CellScore(coord=coord, score=score, reasons=reasons)
  
  
  def _update_hit_clusters(self, coord: Tuple[int, int]):
    """
      Обновляет группы связанных попаданий.
    """
    # Ищем, к какому кластеру относится новое попадание
    merged = False
    for cluster in self.hit_clusters:
      # Если новая клетка соседствует с любой в кластере (по кресту)
      for cr, cc in cluster:
        if abs(coord[0] - cr) + abs(coord[1] - cc) == 1:
          cluster.append(coord)
          merged = True
          break
      if merged:
        break
    
    if not merged:
      self.hit_clusters.append([coord])
  
  
  def get_move(self, board: Board) -> Tuple[int, int]:
    # 1. Приоритет: адаптивное добивание
    if self.hunt_stack:
      state = self.hunt_stack[-1]
      move = self._continue_hunt_adaptive(board, state)
      if move and self._is_valid(board, move):
        return move
      if self.hunt_stack:
        self.hunt_stack.pop()
    
    # 2. Оценка всех необстрелянных клеток
    candidates = []
    for r in range(BOARD_SIZE):
      for c in range(BOARD_SIZE):
        if self._is_valid(board, (r, c)):
          cell_score = self._score_cell(board, (r, c))
          candidates.append(cell_score)
    
    if not candidates:
      return (0, 0)
    
    # 3. Выбираем лучшие + добавляем элемент случайности для непредсказуемости
    candidates.sort(key=lambda x: x.score, reverse=True)
    top_score = candidates[0].score
    top_candidates = [c for c in candidates if c.score >= top_score - 0.5]
    
    chosen = random.choice(top_candidates)
    # Для отладки можно логировать:
    # print(f"Bot chose {chosen.coord} with score {chosen.score:.2f} [{', '.join(chosen.reasons)}]")
    return chosen.coord
  
  
  def handle_shot_result(self, board: Board, coord: Tuple[int, int], result: ShotResult):
    """
      Переопределяем для обновления кластеров попаданий.
    """
    super().handle_shot_result(board, coord, result)
    if result in (ShotResult.HIT, ShotResult.KILL):
      self._update_hit_clusters(coord)
    if result == ShotResult.KILL:
      # Уменьшаем счётчик оставшихся кораблей (упрощённо: по размеру из контекста)
      # В полной версии нужно передавать размер убитого корабля из Board
      pass


# ============================================================================
# КЛАСС БОТА
# ============================================================================

class BotPlayer(Player):
  """
    Игрок-бот с настраиваемым уровнем сложности.
  """
  
  def __init__(self, difficulty: str = "easy"):
    super().__init__(player_id=-1, nickname="BOT", avatar_id=0)
    self.is_bot = True
    self.difficulty = difficulty.lower()
    self.strategy = self._init_strategy()
    self.last_shot_result: Optional[ShotResult] = None
  
  
  def _init_strategy(self) -> BotStrategy:
    """
      Создаёт стратегию в зависимости от уровня сложности.
    """
    strategies = {
      "easy": CheckerboardStrategy,
      "medium": DiagonalStrategy,
      "hard": FeatureBasedStrategy,
    }
    cls = strategies.get(self.difficulty, CheckerboardStrategy)
    return cls()
  
  
  def make_move(self, enemy_board: Board) -> Tuple[int, int]:
    """
      Возвращает координаты следующего выстрела.
    """
    return self.strategy.get_move(enemy_board)
  
  
  def on_shot_result(self, coord: Tuple[int, int], result: ShotResult, enemy_board: Board):
    """
      Вызывается из Game после обработки выстрела.
      Обновляет внутреннее состояние стратегии.
    """
    self.strategy.handle_shot_result(enemy_board, coord, result)
    self.last_shot_result = result