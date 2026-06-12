document.addEventListener('DOMContentLoaded', () => {
  const playerId = localStorage.getItem('player_id');

  if (!playerId) {
    window.location.href = '/';
    return;
  }

  const backBtn = document.getElementById('back-btn');

  // Кнопка "Назад"
  backBtn.addEventListener('click', () => {
    window.navigateWithSound('/menu');
  });
});