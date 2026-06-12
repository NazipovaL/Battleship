document.addEventListener('DOMContentLoaded', () => {
  const titleEl = document.getElementById('result-title');
  const rematchBtn = document.getElementById('rematch-btn');
  const menuBtn = document.getElementById('menu-btn');

  // Читаем результат из URL-параметра (как было в твоей версии)
  const params = new URLSearchParams(window.location.search);
  const result = params.get('result');
  const isWin = result === 'win';

  // Устанавливаем заголовок и стиль
  if (isWin) {
    titleEl.textContent = 'ПОБЕДА!';
    titleEl.classList.add('victory');
  } else {
    titleEl.textContent = 'ПОРАЖЕНИЕ';
    titleEl.classList.add('defeat');

    // Перекрашиваем главную кнопку в красный при поражении
    const primaryBtn = document.querySelector('.btn-result.primary');
    if (primaryBtn) {
      primaryBtn.style.background = '#FF4646';
      primaryBtn.style.borderColor = '#FF4646';
      primaryBtn.style.color = '#fff';
    }
  }

  // Статистика

  // Время игры: считаем от момента старта сессии (если сохранили)
  const startTime = localStorage.getItem('game_start_time');
  if (startTime) {
    const elapsed = Math.floor((Date.now() - parseInt(startTime)) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    document.getElementById('stat-time').textContent = 
      `${minutes}:${seconds.toString().padStart(2, '0')}`;
  }

  // Ходы и точность: читаем из localStorage, если game-process.js их сохраняет
  const stats = JSON.parse(localStorage.getItem('gameStats') || '{}');
  if (stats.moves) {
    document.getElementById('stat-moves').textContent = stats.moves;
  }
  if (stats.accuracy) {
    document.getElementById('stat-accuracy').textContent = stats.accuracy;
  }

  // Кнопки

  rematchBtn.addEventListener('click', () => {
    cleanupAndRedirect('/game-mode');
  });

  menuBtn.addEventListener('click', () => {
    cleanupAndRedirect('/menu');
  });

  // Очистка всех данных сессии
  function cleanupAndRedirect(url) {

    // Данные игры
    localStorage.removeItem('battleship_session_code');
    localStorage.removeItem('battleship_placement');

    // Данные статистики
    localStorage.removeItem('gameResult');
    localStorage.removeItem('gameStats');
    localStorage.removeItem('game_start_time');
    
    window.location.href = url;
  }
});