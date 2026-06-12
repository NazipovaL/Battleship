document.addEventListener('DOMContentLoaded', async () => {
  const playerId = localStorage.getItem('player_id');
  const codeDisplay = document.getElementById('game-code');
  const copyBtn = document.getElementById('copy-btn');
  const backBtn = document.getElementById('back-btn');

  if (!playerId) {
    window.location.href = '/';
    return;
  }

  
  function generateGameCode() {
    const letters = 'ABCDEFGHJKLMNPQRSTUVWXYZ'; 
    const numbers = '0123456789';

    let code = '';
    for (let i = 0; i < 4; i++) {
      code += letters[Math.floor(Math.random() * letters.length)];
    }
    code += '-';
    for (let i = 0; i < 4; i++) {
      code += numbers[Math.floor(Math.random() * numbers.length)];
    }
    return code;
  }


  const sessionCode = generateGameCode();

  const response = await fetch('/api/game/create/online', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      player_id: parseInt(playerId),
      session_code: sessionCode
    })
  });

  const data = await response.json();

  localStorage.setItem('battleship_session_code', sessionCode);
  codeDisplay.textContent = sessionCode;

  async function waitForPlayer() {
    try {
      // Добавлен player_id в URL
      const res = await fetch(`/api/game/state/${sessionCode}/${playerId}`);
      const data = await res.json();

      // Проверяем успешность запроса и наличие второго игрока
      if (data.success && data.enemy_board !== null) {
        // window.location.href = '/ship-placement';
        window.navigateWithSound('/ship-placement');
        return;
      }
    } catch (error) {
      console.error('Ошибка проверки состояния:', error);
    }

    setTimeout(waitForPlayer, 2000);
  }

  waitForPlayer();

  copyBtn.addEventListener('click', () => {
    navigator.clipboard.writeText(sessionCode);
  });


  backBtn.addEventListener('click', () => {
    // window.location.href = '/menu';
    window.navigateWithSound('/menu');
  });
});