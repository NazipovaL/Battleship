document.addEventListener('DOMContentLoaded', () => {
  const backBtn = document.getElementById('back-btn');
  const forwardBtn = document.getElementById('forward-btn');

  // Кнопка "Назад"
  backBtn.addEventListener('click', () => {
    window.location.href = '/game-mode';
  });


  // Кнопка "Вперед"
  forwardBtn.addEventListener('click', async () => {
    console.log('CLICK');

    // Получаем значение выбранной radio-кнопки
    const selectedRadio = document.querySelector('input[name="difficulty"]:checked');
    const difficulty = selectedRadio ? selectedRadio.value : 'medium';

    const playerId = localStorage.getItem('player_id');

    console.log('1. Выбранная сложность:', difficulty);
    console.log('2. Player ID из localStorage:', playerId);

    if (!playerId) {
      alert('Ошибка: игрок не найден');
      window.location.href = '/';
      return;
    }

    try {
      console.log('3. Отправка запроса на сервер...');
      const response = await fetch('/api/game/create/local', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          player_id: parseInt(playerId),
          difficulty: difficulty
        })
      });
      console.log('4. Статус ответа:', response.status);

      const data = await response.json();

      console.log('5. CREATE GAME RESPONSE:', data);
      console.log('6. success =', data.success);
      console.log('7. session_code =', data.session_code);

      if (data.success && data.session_code) {
        localStorage.setItem('battleship_session_code', data.session_code);
        console.log('8. СЕССИЯ СОХРАНЕНА:', data.session_code);

        window.location.href = '/ship-placement';
      } else {
        console.error('INVALID SESSION:', data);
        alert('Ошибка: сервер не вернул session_code');
      }

    } catch (error) {
      console.error('Ошибка:', error);
      alert('Ошибка соединения с сервером');
    }
  });
});