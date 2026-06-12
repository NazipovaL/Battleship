document.addEventListener('DOMContentLoaded', () => {
  const playerId = localStorage.getItem('player_id');

  if (!playerId) {
    window.location.href = '/';
    return;
  }
  
  const modeButtons = document.querySelectorAll('.btn-mode');
  const backBtn = document.getElementById('back-btn');


  // Обработка выбора режима
  modeButtons.forEach(button => {
    button.addEventListener('click', () => {
      const mode = button.getAttribute('data-mode');
      
      if (mode === 'online') {
        window.navigateWithSound('/create-game');
      } 

      if (mode === 'local') {
        window.navigateWithSound('/ai-settings');
      } 
    });
  });


  // Кнопка "Назад"
  backBtn.addEventListener('click', () => {
    window.navigateWithSound('/menu');
  });
});