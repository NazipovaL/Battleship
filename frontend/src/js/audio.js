const bgMusic = new Audio('assets/audio/music.mp3');
const hitSound = new Audio('assets/audio/hit.mp3');
const missSound = new Audio('assets/audio/miss.mp3');
const clickSound = new Audio('assets/audio/click.mp3');

// Настройки
bgMusic.loop = true;
bgMusic.volume = 0.4;
hitSound.volume = 0.7;
missSound.volume = 0.6;
clickSound.volume = 0.4;

// Предзагрузка для мгновенного воспроизведения
bgMusic.preload = 'auto';
hitSound.preload = 'auto';
missSound.preload = 'auto';
clickSound.preload = 'auto';

// Состояние из localStorage 
let isMusicOn = localStorage.getItem('music_on') !== 'false';
let isSoundOn = localStorage.getItem('sound_on') !== 'false';


// Включить/выключить музыку
window.toggleMusic = function(enabled) {
  isMusicOn = enabled;
  localStorage.setItem('music_on', enabled ? 'true' : 'false');
  
  if (enabled) {
    // Восстанавливаем время и запускаем
    const savedTime = parseFloat(localStorage.getItem('music_time') || '0');
    bgMusic.currentTime = savedTime;
    bgMusic.play().catch(() => {});
  } else {
    localStorage.setItem('music_time', bgMusic.currentTime);
    bgMusic.pause();
  }
};

// Включить/выключить звуки эффектов
window.toggleSound = function(enabled) {
  isSoundOn = enabled;
  localStorage.setItem('sound_on', enabled ? 'true' : 'false');
};

// звук попадания
window.playHitSound = function() {
  if (!isSoundOn) return;
  hitSound.currentTime = 0;
  hitSound.play().catch(() => {});
};

// звук промаха
window.playMissSound = function() {
  if (!isSoundOn) return;
  missSound.currentTime = 0;
  missSound.play().catch(() => {});
};

// звук клика
window.playClickSound = function() {
  if (!isSoundOn) return;
  clickSound.currentTime = 0;
  clickSound.play().catch(() => {});
};


window.startMusic = function() {
  if (isMusicOn) {
    const savedTime = parseFloat(localStorage.getItem('music_time') || '0');
    bgMusic.currentTime = savedTime;
    bgMusic.play().catch(() => {});
  }
};

// ИНИЦИАЛИЗАЦИЯ

function initAudio() {
  // Восстанавливаем время музыки при загрузке страницы
  if (isMusicOn) {
    const savedTime = parseFloat(localStorage.getItem('music_time') || '0');
    bgMusic.currentTime = savedTime;
    bgMusic.play().catch(() => {
      console.log('Autoplay blocked. Ожидание клика пользователя...');
    });
  }
  
  // Сохраняем время музыки каждые 500мс
  setInterval(() => {
    if (!bgMusic.paused && !bgMusic.ended) {
      localStorage.setItem('music_time', bgMusic.currentTime);
    }
  }, 50);
  
  // Сохраняем время перед переходом на другую страницу
  window.addEventListener('beforeunload', () => {
    localStorage.setItem('music_time', bgMusic.currentTime);
  });
  
  document.addEventListener('click', function unlockAudio() {
    if (isMusicOn && bgMusic.paused) {
      const savedTime = parseFloat(localStorage.getItem('music_time') || '0');
      bgMusic.currentTime = savedTime;
      bgMusic.play().catch(() => {});
    }
    // Удаляем слушатель после первого срабатывания
    document.removeEventListener('click', unlockAudio);
  }, { once: true });
}

initAudio();

// клик при нажатии на интерактивные элементы
document.addEventListener('click', (e) => {
  const isInteractive = e.target.matches(`
    button, a[href], 
    .nav-arrow, .ship-container, 
    .dropdown-item, input[type="submit"],
    .settings-btn, .btn-surrender, .btn-result, .btn-control,
    .register-button, .btn-nav, .btn-forward, .btn-back,
    .btn, .logout-btn, .btn-mode, #close-modal-btn, .btn-submit,
    .btn--large, .btn--small, .logout-btn, .btn-control,
    .btn-result
  `);
  
  if (isInteractive && window.playClickSound) {
    window.playClickSound();
  }
});


// НАДЁЖНЫЙ перехват переходов
document.addEventListener('click', (e) => {
  const button = e.target.closest(`
    .btn,
    .btn--large,
    .btn--small,
    .logout-btn,
    .register-button
  `);

  if (!button) return;

  // перехватываем ТОЛЬКО если есть переход
  const hasNavigation =
    button.onclick ||
    button.dataset.href ||
    button.getAttribute('href');

  if (!hasNavigation) return;

  e.preventDefault();

  if (window.playClickSound) {
    window.playClickSound();
  }

  // небольшая задержка, чтобы звук реально успел стартовать
  setTimeout(() => {
    if (button.onclick) {
      button.onclick();
    } else if (button.dataset.href) {
      window.location.href = button.dataset.href;
    } else if (button.getAttribute('href')) {
      window.location.href = button.getAttribute('href');
    }
  }, 150);
});


// универсальный переход со звуком
window.navigateWithSound = function(url) {
  if (window.playClickSound) {
    window.playClickSound();
  }

  setTimeout(() => {
    window.location.href = url;
  }, 120); // 100–150мс — sweet spot
};
