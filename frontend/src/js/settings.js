document.addEventListener('DOMContentLoaded', () => {
  const playerId = localStorage.getItem('player_id');

  if (!playerId) {
    window.location.href = '/';
    return;
  }

  const musicToggle = document.getElementById('music-toggle');
  const soundToggle = document.getElementById('sound-toggle');

  musicToggle.checked = localStorage.getItem('music_on') !== 'false';
  soundToggle.checked = localStorage.getItem('sound_on') !== 'false';


  // ОБРАБОТЧИКИ
  
  musicToggle.addEventListener('change', () => {
    window.toggleMusic(musicToggle.checked);
  });

  soundToggle.addEventListener('change', () => {
    window.toggleSound(soundToggle.checked);
  });

  const saveBtn = document.getElementById('save-btn'); 
  saveBtn.onclick = () => window.navigateWithSound('/menu');
});