document.addEventListener('DOMContentLoaded', async () => {
  let playerBoard = [];
  let enemyBoard = Array(100).fill(null);
  let isPlayerTurn = true;
  let gameActive = true;
  let sessionCode = null;
  let ws = null;

  // Засекаем время начала игры
  localStorage.setItem('game_start_time', Date.now().toString());

  // Счётчики для статистики
  let gameStats = {
    moves: 0,
    hits: 0,
    shots: 0
  };

  const urlParams = new URLSearchParams(window.location.search);
  sessionCode = urlParams.get('session') || localStorage.getItem('battleship_session_code');

  if (!sessionCode) {
    console.error('No session code found');
    alert('Ошибка: сессия не найдена. Пожалуйста, начните игру заново.');
    window.location.href = '/menu';
    return;
  }

  localStorage.setItem('battleship_session_code', sessionCode);

  const savedPlacement = localStorage.getItem('battleship_placement');
  if (savedPlacement) {
    playerBoard = JSON.parse(savedPlacement);
  } else {
    playerBoard = Array(100).fill(null);
  }

  const playerGrid = document.getElementById('player-grid');
  const enemyGrid = document.getElementById('enemy-grid');
  const turnIndicator = document.getElementById('game-status');
  const giveUpBtn = document.getElementById('surrender-btn');


  // WebSocket подключение
  function connectWebSocket() {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const playerId = localStorage.getItem('player_id');
    const wsUrl = `${wsProtocol}//${window.location.host}/api/game/ws/${sessionCode}?player_id=${playerId}`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket подключен');
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      handleWebSocketMessage(message);
    };

    ws.onerror = (error) => {
      console.error('WebSocket ошибка:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket отключен');
      setTimeout(connectWebSocket, 3000);
    };
  }


  async function handleWebSocketMessage(message) {
    const { type, data } = message;

    switch (type) {
      case 'init_state':
        console.log('Получено начальное состояние:', data);
        if (data.player_board) {
          playerBoard = data.player_board;
          createPlayerGrid();
        }
        if (data.enemy_board) {
          enemyBoard = data.enemy_board;
          createEnemyGrid();
        }
        isPlayerTurn = data.is_player_turn;
        gameActive = !data.game_over;

        if (data.game_over) {
          turnIndicator.textContent = data.winner ? 'ПОБЕДА!' : 'ПОРАЖЕНИЕ!';
        } else if (data.ready_count < 2) {
          turnIndicator.textContent = 'Ожидание готовности игроков...';
        } else {
          turnIndicator.textContent = isPlayerTurn ? 'Ваш ход!' : 'Ход противника...';
        }
        renderPlayers(data.player, data.enemy);
        break;

      case 'player_joined':
        console.log('Игрок присоединился:', data.nickname);
        turnIndicator.textContent = 'Игрок присоединился! Ожидание готовности...';
        break;

      case 'player_ready':
        console.log('Игрок готов:', data.player_id, 'Готово:', data.ready_count);
        if (data.ready_count === 1) {
          turnIndicator.textContent = 'Ожидание второго игрока...';
        }
        break;

      case 'game_start':
        console.log('Игра началась!');
        turnIndicator.textContent = 'Игра началась! Ваш ход!';
        break;

      case 'move_made':
        console.log('Ход сделан:', data);
        const index = data.x * 10 + data.y;

        if (data.player_id === parseInt(localStorage.getItem('player_id'))) {
          if (data.result === 'hit' || data.result === 'kill') {
            window.playHitSound();
            enemyBoard[index] = 'hit';
            updateCellVisual(enemyGrid, index, 'hit');

            if (data.result === 'kill') {
              turnIndicator.textContent = 'Корабль уничтожен! Ещё ход!';
              // Загрузить актуальное состояние поля (вокруг убитого корабля появились точки)
              await loadGameState();
            } else {
              turnIndicator.textContent = 'Попадание! Ещё ход!';
            }
          } else {
            window.playMissSound();
            enemyBoard[index] = 'miss';
            updateCellVisual(enemyGrid, index, 'miss');
            isPlayerTurn = false;
            turnIndicator.textContent = 'Промах! Ход противника...';
            turnIndicator.classList.add('enemy-turn');
          }
        } else {
          if (data.result === 'hit' || data.result === 'kill') {
            window.playHitSound(); 
            playerBoard[index] = 'hit';
            updateCellVisual(playerGrid, index, 'ship-hit');  // ← было 'hit'

            if (data.result === 'kill') {
              turnIndicator.textContent = 'Противник уничтожил ваш корабль! Его ход продолжается...';
              await loadGameState();
            } else {
              turnIndicator.textContent = 'Противник попал! Его ход продолжается...';
            }
          } else {
            window.playMissSound();
            playerBoard[index] = 'miss';
            updateCellVisual(playerGrid, index, 'miss');
            isPlayerTurn = true;
            turnIndicator.textContent = 'Противник промахнулся! Ваш ход!';
            turnIndicator.classList.remove('enemy-turn');
          }
        }

        if (data.game_over) {
          gameActive = false;
        }
        break;

      case 'game_over':
        console.log('Игра окончена! Победитель:', data.winner_nickname);
        gameActive = false;
        const myId = parseInt(localStorage.getItem('player_id'));
        if (data.winner_id === myId) {
          turnIndicator.textContent = 'ПОБЕДА!';
          setTimeout(() => {
            window.location.href = '/winner?result=win';
          }, 1500);
        } else {
          turnIndicator.textContent = 'ПОРАЖЕНИЕ!';
          setTimeout(() => {
            window.location.href = '/winner?result=loss';
          }, 1500);
        }
        break;

      case 'player_disconnected':
        console.log('Игрок отключился:', data.player_id);
        turnIndicator.textContent = 'Противник отключился от игры!';
        gameActive = false;
        break;

      case 'error':
        console.error('Ошибка от сервера:', data.message);
        alert(data.message);
        break;
    }
  }


  function createPlayerGrid() {
    playerGrid.innerHTML = '';
    for (let i = 0; i < 100; i++) {
      const cell = document.createElement('div');
      cell.classList.add('cell');
      cell.dataset.index = i;

      // playerBoard содержит: null, 'ship', 'hit' (попал по кораблю), 'miss'
      if (playerBoard[i] === 'ship') {
        cell.classList.add('ship');
      } else if (playerBoard[i] === 'hit') {
        cell.classList.add('ship-hit');   // было 'hit'
      } else if (playerBoard[i] === 'miss') {
        cell.classList.add('miss');
      }

      playerGrid.appendChild(cell);
    }
  }


  function createEnemyGrid() {
    enemyGrid.innerHTML = '';
    for (let i = 0; i < 100; i++) {
      const cell = document.createElement('div');
      cell.classList.add('cell');
      cell.dataset.index = i;

      if (enemyBoard[i] === 'hit') {
        cell.classList.add('hit');
      } else if (enemyBoard[i] === 'miss') {
        cell.classList.add('miss');
      }

      cell.addEventListener('click', () => onCellClick(i));
      enemyGrid.appendChild(cell);
    }
  }


  async function onCellClick(index) {
    if (!gameActive || !isPlayerTurn) {
      alert('Сейчас не ваш ход!');
      return;
    }

    if (enemyBoard[index] === 'hit' || enemyBoard[index] === 'miss') {
      alert('Вы уже стреляли в эту клетку!');
      return;
    }

    const x = Math.floor(index / 10);
    const y = index % 10;

    // Отправить выстрел через WebSocket
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'move',
        data: {
          session_code: sessionCode,
          player_id: parseInt(localStorage.getItem('player_id')),
          x: x,
          y: y
        }
      }));
    } else {
      // Fallback на REST API если WebSocket недоступен
      try {
        const playerId = localStorage.getItem('player_id');
        const response = await fetch('/api/game/shoot', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_code: sessionCode,
            player_id: parseInt(playerId),
            x: x,
            y: y
          })
        });

        const data = await response.json();

        if (data.success) {
          gameStats.shots++;
          if (data.result === 'hit' || data.result === 'kill') {
            window.playHitSound();
            gameStats.hits++;
            enemyBoard[index] = 'hit';
            updateCellVisual(enemyGrid, index, 'hit');

            if (data.result === 'kill') {
              turnIndicator.textContent = 'Корабль уничтожен! Ещё ход!';
              await loadGameState();
            } else {
              turnIndicator.textContent = 'Попадание! Ещё ход!';
            }

            if (data.game_over) {
              gameActive = false;
              turnIndicator.textContent = 'ПОБЕДА! Вы уничтожили все корабли!';
              setTimeout(() => {
                window.location.href = '/winner?result=win';
              }, 1500);
              return;
            }
          } else {
            window.playHitSound();
            enemyBoard[index] = 'miss';
            updateCellVisual(enemyGrid, index, 'miss');
            isPlayerTurn = false;
            turnIndicator.textContent = 'Промах! Ход противника...';
          }
          gameStats.moves++;
          localStorage.setItem('gameStats', JSON.stringify({
            moves: gameStats.moves,
            accuracy: gameStats.shots > 0
              ? Math.round((gameStats.hits / gameStats.shots) * 100) + '%'
              : '0%'
          }));
        } else {
          alert(data.message || 'Ошибка при выстреле');
        }
      } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка соединения с сервером');
      }
    }
  }


  function updateCellVisual(grid, index, type) {
    const cell = grid.querySelector(`[data-index="${index}"]`);
    if (cell) {
      cell.classList.add(type);
    }
  }


  async function loadGameState() {
    if (!gameActive) return;

    try {
      const playerId = localStorage.getItem('player_id');
      const response = await fetch(`/api/game/state/${sessionCode}/${playerId}`);
      const data = await response.json();

      if (data.success) {
        renderPlayers(data.player, data.enemy);
        if (data.player_board) {
          playerBoard = data.player_board;
          createPlayerGrid();
        }
        if (data.enemy_board) {
          enemyBoard = data.enemy_board;
          createEnemyGrid();
        }
        isPlayerTurn = data.is_player_turn;
        gameActive = !data.game_over;

        if (data.game_over) {
          turnIndicator.textContent = data.winner ? 'ПОБЕДА!' : 'ПОРАЖЕНИЕ!';
        } else {
          turnIndicator.textContent = isPlayerTurn ? 'Ваш ход!' : 'Ход противника...';
        }
      }
    } catch (error) {
      console.error('Ошибка загрузки состояния:', error);
    }
  }


  async function initGame() {
    connectWebSocket();
    await loadGameState();
    createPlayerGrid();
    createEnemyGrid();
  }


  giveUpBtn.addEventListener('click', async () => {
    if (confirm('Вы уверены, что хотите сдаться?')) {
      try {
        await fetch('/api/game/give-up', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_code: sessionCode,
            player_id: parseInt(localStorage.getItem('player_id'))
          })
        });
        gameActive = false;
        turnIndicator.textContent = 'Вы сдались! Поражение!';
        window.location.href = '/winner?result=loss';
      } catch (error) {
        console.error('Ошибка:', error);
        window.location.href = '/winner?result=loss';
      }
    }
  });

  initGame();

  // Модальное окно настроек
  const settingsModal = document.getElementById('settings-modal');
  const closeModalBtn = document.getElementById('close-modal-btn');

  document.getElementById('settings-btn').addEventListener('click', () => {
    settingsModal.classList.add('active');
  });

  if (closeModalBtn) {
    closeModalBtn.addEventListener('click', () => {
      settingsModal.classList.remove('active');
    });
  }

  settingsModal.addEventListener('click', (e) => {
    if (e.target === settingsModal) {
      settingsModal.classList.remove('active');
    }
  });

  
  const musicToggle = document.getElementById('music-toggle');
  const soundToggle = document.getElementById('sound-toggle');

  if (musicToggle && soundToggle) {
    // начальное состояние
    musicToggle.checked = localStorage.getItem('music_on') !== 'false';
    soundToggle.checked = localStorage.getItem('sound_on') !== 'false';

    musicToggle.addEventListener('change', () => {
      window.toggleMusic(musicToggle.checked);
    });

    soundToggle.addEventListener('change', () => {
      window.toggleSound(soundToggle.checked);
    });
  }


  // Кнопка сдаться
  giveUpBtn.addEventListener('click', async () => {
    if (confirm('⚠️ Вы уверены, что хотите сдаться?')) {
      try {
        await fetch('/api/game/give-up', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_code: sessionCode,
            player_id: parseInt(localStorage.getItem('player_id'))
          })
        });
        gameActive = false;
        turnIndicator.textContent = 'Вы сдались! Поражение!';
        window.location.href = '/winner?result=loss';
      } catch (error) {
        console.error('Ошибка:', error);
        window.location.href = '/winner?result=loss';
      }
    }
  });

  function renderPlayers(player, enemy) {
    if (player) {
      document.getElementById('player-nickname').textContent = player.nickname;
      document.getElementById('player-avatar').style.backgroundImage = `url(/assets/images/avatars/avatar-${player.avatar_id + 1}.png`;
    }

    if (enemy) {
      document.getElementById('enemy-nickname').textContent = enemy.nickname;
      document.getElementById('enemy-avatar').style.backgroundImage = `url(/assets/images/avatars/avatar-${player.avatar_id + 1}.png`;
    }
  }
});