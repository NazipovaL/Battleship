document.addEventListener('DOMContentLoaded', () => {
  const sessionCode = localStorage.getItem('battleship_session_code');

  if (!sessionCode || sessionCode === 'undefined') {
    console.error('SESSION LOST');
    alert('Сессия потеряна. Начните игру заново.');
    // window.location.href = '/game-mode';
    window.navigateWithSound('/game-mode');
  }


  const grid = document.getElementById('battle-grid');
  const shipsPanel = document.querySelector('.ships-panel');
  const ships = document.querySelectorAll('.ship-container');
  const rotateBtn = document.getElementById('rotate-btn');

  let currentShipClone = null;
  let currentShipOriginal = null;
  let currentSize = 0;
  let isHorizontal = true;
  let currentShipId = null;

  const board = Array(100).fill(null);

  // Генерация поля 10x10
  for (let i = 0; i < 100; i++) {
    const cell = document.createElement('div');
    cell.classList.add('grid-cell');
    cell.dataset.index = i;
    grid.appendChild(cell);
  }


  // Функция удаления клона
  function removeClone() {
    if (currentShipClone && currentShipClone.parentNode) {
      currentShipClone.remove();
    }
    currentShipClone = null;
  }


  // Функция отмены перетаскивания
  function cancelDrag() {
    if (currentShipClone) {
      removeClone();
    }

    if (currentShipOriginal) {
      currentShipOriginal.style.opacity = '1';
      currentShipOriginal.style.pointerEvents = 'auto';
      currentShipOriginal = null;
    }

    currentSize = 0;
    currentShipId = null;
    isHorizontal = true;
    clearHighlights();
  }


  // Функция позиционирования клона под курсором
  function positionCloneAtCursor(e) {
    if (!currentShipClone) return;

    const cloneRect = currentShipClone.getBoundingClientRect();
    let left = e.clientX - cloneRect.width / 2;
    let top = e.clientY - cloneRect.height / 2;

    left = Math.max(0, Math.min(window.innerWidth - cloneRect.width, left));
    top = Math.max(0, Math.min(window.innerHeight - cloneRect.height, top));

    currentShipClone.style.left = left + 'px';
    currentShipClone.style.top = top + 'px';
  }


  // Создание клона корабля
  function createShipClone(ship, size, horizontal) {
    const clone = ship.cloneNode(true);
    clone.id = 'dragging-ship-clone';
    clone.classList.add('dragging');
    clone.setAttribute('data-size', size);
    clone.style.position = 'fixed';
    clone.style.zIndex = '9999';
    clone.style.cursor = 'grabbing';
    clone.style.pointerEvents = 'none'; // ВАЖНО: чтобы клон не перехватывал клики
    clone.style.margin = '0';
    clone.style.opacity = '0.9';

    if (!horizontal) {
      clone.style.transform = 'rotate(90deg)';
      clone.style.width = '40px';
      clone.style.height = (size * 40) + 'px';
    } else {
      clone.style.transform = 'rotate(0deg)';
      clone.style.width = '';
      clone.style.height = '';
    }

    return clone;
  }


  // "Корабль в руке" по ПКМ
  ships.forEach(ship => {
    ship.setAttribute('draggable', 'false');

    ship.addEventListener('contextmenu', (e) => {
      e.preventDefault();
      e.stopPropagation();

      if (currentShipClone) {
        cancelDrag();
      }

      if (ship.classList.contains('placed')) {
        const shipId = ship.dataset.id;
        for (let i = 0; i < board.length; i++) {
          if (board[i] === shipId) {
            board[i] = null;
            const cell = document.querySelector(`[data-index="${i}"]`);
            if (cell) cell.classList.remove('occupied');
          }
        }
        ship.classList.remove('placed');
        ship.style.opacity = '1';
      }

      currentShipOriginal = ship;
      currentSize = parseInt(ship.dataset.size);
      currentShipId = ship.dataset.id;
      isHorizontal = true;

      currentShipOriginal.style.opacity = '0';
      currentShipOriginal.style.pointerEvents = 'none';

      currentShipClone = createShipClone(ship, currentSize, isHorizontal);
      document.body.appendChild(currentShipClone);

      positionCloneAtCursor(e);
    });
  });


  // Движение за курсором
  document.addEventListener('mousemove', (e) => {
    if (!currentShipClone) return;
    positionCloneAtCursor(e);
  });


  // Поворот корабля (mouseup вместо click)
  if (rotateBtn) {
    rotateBtn.addEventListener('mouseup', (e) => {
      e.preventDefault();
      e.stopPropagation();

      console.log('Кнопка поворота нажата, currentShipClone:', !!currentShipClone);

      if (!currentShipClone || !currentShipOriginal) return;

      isHorizontal = !isHorizontal;

      if (isHorizontal) {
        currentShipClone.style.transform = 'rotate(0deg)';
        currentShipClone.style.width = '';
        currentShipClone.style.height = '';
      } else {
        currentShipClone.style.transform = 'rotate(90deg)';
        currentShipClone.style.width = '40px';
        currentShipClone.style.height = (currentSize * 40) + 'px';
      }

      console.log('Поворот выполнен, горизонтальный:', isHorizontal);
    });
  }


  // Проверка возможности размещения
  function isValidPlacement(startIndex, size, horizontal) {
    const row = Math.floor(startIndex / 10);
    const col = startIndex % 10;
    let cells = [];

    for (let i = 0; i < size; i++) {
      let r = row;
      let c = col;

      if (horizontal) c += i;
      else r += i;

      if (r >= 10 || c >= 10) return null;

      const index = r * 10 + c;

      for (let dr = -1; dr <= 1; dr++) {
        for (let dc = -1; dc <= 1; dc++) {
          const nr = r + dr;
          const nc = c + dc;

          if (nr >= 0 && nr < 10 && nc >= 0 && nc < 10) {
            const ni = nr * 10 + nc;
            if (board[ni] !== null && !cells.includes(ni)) {
              return null;
            }
          }
        }
      }

      cells.push(index);
    }

    return cells;
  }


  // Подсветка клеток
  function clearHighlights() {
    document.querySelectorAll('.grid-cell.highlight').forEach(cell => {
      cell.classList.remove('highlight');
    });
    document.querySelectorAll('.grid-cell.invalid').forEach(cell => {
      cell.classList.remove('invalid');
    });
  }

  function highlightCells(startIndex, size, horizontal) {
    clearHighlights();

    const validCells = isValidPlacement(startIndex, size, horizontal);

    if (validCells) {
      validCells.forEach(index => {
        const cell = document.querySelector(`[data-index="${index}"]`);
        if (cell) cell.classList.add('highlight');
      });
    } else if (startIndex !== undefined) {
      const row = Math.floor(startIndex / 10);
      const col = startIndex % 10;
      for (let i = 0; i < size; i++) {
        let r = row, c = col;
        if (horizontal) c += i;
        else r += i;
        if (r < 10 && c < 10) {
          const index = r * 10 + c;
          const cell = document.querySelector(`[data-index="${index}"]`);
          if (cell) cell.classList.add('invalid');
        }
      }
    }
  }


  // Подсветка при наведении
  let lastHighlightIndex = -1;

  grid.addEventListener('mousemove', (e) => {
    if (!currentShipClone) return;

    const cell = e.target.closest('.grid-cell');
    if (!cell) {
      clearHighlights();
      return;
    }

    const startIndex = parseInt(cell.dataset.index);
    if (lastHighlightIndex !== startIndex) {
      lastHighlightIndex = startIndex;
      highlightCells(startIndex, currentSize, isHorizontal);
    }
  });

  grid.addEventListener('mouseleave', () => {
    clearHighlights();
  });


  // Размещение корабля (mouseup на поле вместо click)
  grid.addEventListener('mouseup', (e) => {
    if (!currentShipClone || !currentShipOriginal) return;

    const cell = e.target.closest('.grid-cell');
    if (!cell) return;

    const startIndex = parseInt(cell.dataset.index);
    const validCells = isValidPlacement(startIndex, currentSize, isHorizontal);

    console.log('Размещение:', { startIndex, currentSize, isHorizontal, validCells });

    if (!validCells) {
      console.log('Невалидное размещение');
      return;
    }

    validCells.forEach(i => {
      board[i] = currentShipId;
      const gridCell = document.querySelector(`[data-index="${i}"]`);
      if (gridCell) gridCell.classList.add('occupied');
    });

    if (currentShipOriginal) {
      currentShipOriginal.classList.add('placed');
      currentShipOriginal.style.opacity = '0.5';
      currentShipOriginal.style.pointerEvents = 'auto';
    }

    console.log('Корабль размещён успешно');

    removeClone();
    currentShipOriginal = null;
    currentSize = 0;
    currentShipId = null;
    isHorizontal = true;
    clearHighlights();
  });


  // Отмена перетаскивания (ПКМ)
  document.addEventListener('contextmenu', (e) => {
    if (currentShipClone) {
      e.preventDefault();
      cancelDrag();
    }
  });


  // Отмена при клике вне поля и вне кнопки поворота
  document.addEventListener('mouseup', (e) => {
    if (!currentShipClone) return;

    const isOnGrid = e.target.closest('#battle-grid');
    const isOnRotateBtn = e.target.closest('#rotate-btn');
    const isOnShip = e.target.closest('.ship-container');

    if (!isOnGrid && !isOnRotateBtn && !isOnShip) {
      cancelDrag();
    }
  });


  // Удаление корабля с поля (ПКМ по клетке)
  grid.addEventListener('contextmenu', (e) => {
    e.preventDefault();

    if (currentShipClone) {
      cancelDrag();
      return;
    }

    const cell = e.target.closest('.grid-cell');
    if (!cell) return;

    const index = parseInt(cell.dataset.index);
    const shipId = board[index];

    if (!shipId) return;

    for (let i = 0; i < board.length; i++) {
      if (board[i] === shipId) {
        board[i] = null;
        const gridCell = document.querySelector(`[data-index="${i}"]`);
        if (gridCell) gridCell.classList.remove('occupied');
      }
    }

    const ship = document.querySelector(`.ship-container[data-id="${shipId}"]`);
    if (ship) {
      ship.classList.remove('placed');
      ship.style.opacity = '1';
    }
  });


  // Очистка поля
  document.getElementById('clear-btn').addEventListener('click', () => {
    for (let i = 0; i < board.length; i++) {
      board[i] = null;
    }

    document.querySelectorAll('.grid-cell').forEach(cell => {
      cell.classList.remove('occupied');
    });

    ships.forEach(ship => {
      ship.classList.remove('placed');
      ship.style.opacity = '1';
    });

    if (currentShipClone) {
      cancelDrag();
    }
  });


  // Кнопки навигации
  document.getElementById('back-btn').addEventListener('click', () => {
    window.navigateWithSound('/menu');
  });


  let isStarting = false;

  document.getElementById('start-btn').addEventListener('click', async () => {
    // Защита от повторных нажатий
    if (isStarting) return;
    isStarting = true;

    const totalShipCells = 20;
    let placedCells = board.filter(cell => cell !== null).length;

    if (placedCells !== totalShipCells) {
      alert('Разместите все корабли на поле!');
      isStarting = false;
      return;
    }

    // Сохраняем расстановку
    localStorage.setItem('battleship_placement', JSON.stringify(board));

    // Получаем session_code из localStorage
    const sessionCode = localStorage.getItem('battleship_session_code');
    console.log('SESSION:', sessionCode);

    if (!sessionCode) {
      console.error('Session code not found');
      alert('Ошибка: сессия не найдена. Пожалуйста, начните игру заново.');
      window.navigateWithSound('/menu');
      return;
    }

    function convertBoardToShips(board) {
      const shipsMap = {};

      board.forEach((cell, index) => {
        if (!cell) return;

        if (!shipsMap[cell]) {
          shipsMap[cell] = [];
        }

        const row = Math.floor(index / 10);
        const col = index % 10;

        shipsMap[cell].push([row, col]);
      });

      return Object.entries(shipsMap).map(([shipId, coordinates]) => ({
        size: coordinates.length,
        coordinates: coordinates
      }));
    }

    const ships = convertBoardToShips(board);

    try {
      const response = await fetch('/api/game/setup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_code: sessionCode,
          player_id: parseInt(localStorage.getItem('player_id')),
          ships: ships
        })
      });

      const data = await response.json();

      if (!data.success) {
        alert('Ошибка при сохранении');
        isStarting = false;
        return;
      }

      // Для локальной игры
      if (sessionCode.startsWith('LOCAL-')) {
        console.log('Локальная игра - переход на game-process');
        window.navigateWithSound(`/game-process?session=${sessionCode}`);
        return;
      }

      // Для онлайн-игры
      async function waitForReady() {
        const res = await fetch(`/api/game/ready/${sessionCode}`);
        const data = await res.json();

        if (data.ready) {
          window.navigateWithSound(`/game-process?session=${sessionCode}`);
        } else {
          setTimeout(waitForReady, 2000);
        }
      }

      waitForReady();

    } catch (error) {
      console.error('Ошибка:', error);
      alert('Ошибка соединения с сервером');
      isStarting = false;
    }
  });

  const dropdownToggle = document.getElementById('dropdown-toggle');
  const dropdownMenu = document.getElementById('dropdown-menu');
  const dropdownItems = document.querySelectorAll('.dropdown-item');

  // открыть / закрыть меню
  dropdownToggle.addEventListener('click', (e) => {
    e.stopPropagation();
    dropdownMenu.classList.toggle('active');
  });


  // закрытие при клике вне
  document.addEventListener('click', (e) => {
    if (!dropdownToggle.contains(e.target) && !dropdownMenu.contains(e.target)) {
      dropdownMenu.classList.remove('active');
    }
  });


  // генерация расстановки
  dropdownItems.forEach(item => {
    item.addEventListener('click', async (e) => {
      e.stopPropagation();

      const strategyMap = {
        random: 'random',
        edges: 'edge',
        diagonal: 'cluster'
      };

      const strategy = strategyMap[item.dataset.strategy];

      dropdownMenu.classList.remove('active');

      try {
        // const response = await fetch(`http://127.0.0.1:8001/api/generate-board?strategy=${strategy}`)
        const response = await fetch(`/api/generate-board?strategy=${strategy}`)
        const data = await response.json();

        applyGeneratedBoard(data);
      } catch (err) {
        console.error('Ошибка генерации:', err);
        alert('Не удалось сгенерировать поле');
      }
    });
  });

  
  // применить расстановку на поле
  function applyGeneratedBoard(data) {
    // очистка
    for (let i = 0; i < board.length; i++) {
      board[i] = null;
    }

    document.querySelectorAll('.grid-cell').forEach(cell => {
      cell.classList.remove('occupied');
    });

    ships.forEach(ship => {
      ship.classList.remove('placed');
      ship.style.opacity = '1';
    });

    // заполнение
    const shipsData = data.ships;

    Object.entries(shipsData).forEach(([size, shipsList]) => {
      shipsList.forEach((shipCoords, index) => {
        const shipId = `ship-${size}-${index + 1}`;
        const ship = document.querySelector(`[data-id="${shipId}"]`);

        if (!ship) return;

        ship.classList.add('placed');
        ship.style.opacity = '0.5';

        shipCoords.forEach(coord => {
          const match = coord.match(/(\d+)([А-Я])/);
          if (!match) return;

          const row = parseInt(match[1]) - 1;
          const col = data.columns.indexOf(match[2]);

          const index = row * 10 + col;

          board[index] = shipId;

          const cell = document.querySelector(`[data-index="${index}"]`);
          if (cell) cell.classList.add('occupied');
        });
      });
    });
  }


});