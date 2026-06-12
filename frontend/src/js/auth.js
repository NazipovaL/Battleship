document.addEventListener('DOMContentLoaded', function () {

  let selectedAvatarIndex = 0;

  // Инициализация Swiper карусели
  const avatarSwiper = new Swiper('.avatar-swiper', {
    slidesPerView: 3,
    spaceBetween: 15,
    loop: true,
    centeredSlides: true,
    speed: 300,

    navigation: {
      nextEl: '.arrow-right',
      prevEl: '.arrow-left',
    },

    on: {
      init: function () {
        updateActiveAvatar(this.realIndex);
      },
      slideChange: function () {
        updateActiveAvatar(this.realIndex);
      },
    },
  });

  function updateActiveAvatar(index) {
    selectedAvatarIndex = index;
    console.log('Выбран аватар:', index + 1);
  }

  // Клик по кружку
  document.querySelectorAll('.avatar-circle').forEach((circle, index) => {
    circle.addEventListener('click', () => {
      avatarSwiper.slideToLoop(index, 300);
    });
  });


  // Форма регистрации
  const form = document.querySelector('.registration-form');

  function validateForm(nickname) {
    if (!nickname) {
      return 'Введите никнейм';
    }

    if (nickname.length < 4 || nickname.length > 8) {
      return 'Никнейм должен быть от 4 до 8 символов';
    }
    return null;
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const nickname = document.getElementById('nickname').value.trim();

    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }

    try {
      const result = await api.login(nickname, selectedAvatarIndex);

      if (result.success) {
        // window.location.href = '/menu';
        window.navigateWithSound('/menu');
      } else {
        alert(result.message);
      }

    } catch (err) {
      console.error(err);
      alert('Ошибка соединения с сервером');
    }
  });
});