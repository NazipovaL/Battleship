document.addEventListener('DOMContentLoaded', async function () {
  const nickname = localStorage.getItem('nickname') || 'ИГРОК';
  const avatarIndex = parseInt(localStorage.getItem('avatar_id')) || 0;

  document.getElementById('user-nickname').textContent = nickname;

  // Кнопки

  const largeButtons = document.querySelectorAll('.btn--large');
  // largeButtons[0].onclick = () => window.location.href = '/game-mode';
  // largeButtons[1].onclick = () => window.location.href = '/join-game';

  const smallButtons = document.querySelectorAll('.btn--small');
  // smallButtons[0].onclick = () => window.location.href = '/rules';
  // smallButtons[1].onclick = () => window.location.href = '/settings';
  // smallButtons[2].onclick = () => window.location.href = '/about-system';
  // smallButtons[3].onclick = () => window.location.href = '/about-authors';

  largeButtons[0].dataset.href = '/game-mode';
  largeButtons[1].dataset.href = '/join-game';

  smallButtons[0].dataset.href = '/rules';
  smallButtons[1].dataset.href = '/settings';
  smallButtons[2].dataset.href = '/about-system';
  smallButtons[3].dataset.href = '/about-authors';

  // Аватар

  const avatarContainer = document.getElementById('user-avatar');
  avatarContainer.innerHTML = '';
  const avatarCircle = document.createElement('div');

  avatarCircle.className = 'avatar-item avatar-item--active';
  avatarCircle.style.width = '90px';
  avatarCircle.style.height = '90px';

  document.getElementById('player-avatar').style.backgroundImage = `url(/assets/images/avatars/avatar-${player.avatar_id + 1}.png`;
  avatarContainer.style.backgroundImage = `url(/assets/images/avatars/avatar-${player.avatar_id + 1}.png`;
 
  avatarCircle.style.display = 'flex';
  avatarCircle.style.alignItems = 'center';
  avatarCircle.style.justifyContent = 'center';
  avatarCircle.style.fontSize = '28px';
  avatarCircle.style.fontWeight = 'bold';
  avatarCircle.style.color = '#85FBFF';
  avatarCircle.style.fontFamily = 'Inter, sans-serif';

  avatarContainer.appendChild(avatarCircle);
  console.log('Меню загружено. Игрок:', nickname, 'Аватар:', avatarIndex);


  // Разлогиниться

  const logoutBtn = document.getElementById('logout-btn');

  if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
      try {
        const result = await api.logout();

        if (!result.success) {
          console.warn('Логаут не удался:', result.message);
        }

      } catch (error) {
        console.error('Ошибка при выходе:', error);
      }
      api.clearPlayer();
      window.location.href = '/';
    });
  }

});