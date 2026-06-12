document.addEventListener('DOMContentLoaded', () => {
  const playerId = localStorage.getItem('player_id');

  if (!playerId) {
    window.location.href = '/';
    return;
  }

  const codeInput = document.getElementById('game-code-input');
  const joinBtn = document.getElementById('join-btn');
  const backBtn = document.getElementById('back-btn');

  // Автоформатирование ввода
  codeInput.addEventListener('input', (e) => {
    let value = e.target.value.toUpperCase();
    if (value.length === 4 && !value.includes('-')) {
      value += '-';
    }

    value = value.replace(/[^A-Z0-9-]/g, '');
    e.target.value = value;
  });


  // Кнопка "Назад"
  backBtn.addEventListener('click', () => {
    window.navigateWithSound('/menu');
  });


  joinBtn.addEventListener('click', async () => {
    const code = codeInput.value.trim();
    const playerId = localStorage.getItem('player_id');

    const response = await fetch('/api/game/join', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_code: code,
        player_id: parseInt(playerId)
      })
    });

    const data = await response.json();

    if (data.success) {
      localStorage.setItem('battleship_session_code', code);
      window.navigateWithSound('/ship-placement');
    } else {
      alert(data.message);
    }
  });
});