const API_BASE = '/api';

class BattleShipAPI {
  constructor() {
    this.playerId = localStorage.getItem('player_id');
  }

  setPlayer(playerId, nickname, avatar_id) {
    this.playerId = playerId;
    localStorage.setItem('player_id', playerId);
    localStorage.setItem('nickname', nickname);
    localStorage.setItem('avatar_id', avatar_id);

  }

  clearPlayer() {
    this.playerId = null;
    localStorage.removeItem('player_id');
    localStorage.removeItem('nickname');
    localStorage.removeItem('avatar_id');
  }

  async login(nickname, avatarId) {
    const response = await fetch(`/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nickname, avatar_id: avatarId })
    });

    const data = await response.json();

    if (data.success) {
      this.setPlayer(data.player_id, nickname, avatarId);
    }

    return data;
  }

  async logout() {
    const response = await fetch(`/api/auth/logout?player_id=${this.playerId}`, {
      method: 'POST'
    });

    const data = await response.json();

    if (data.success) {
      this.clearPlayer();
    }

    return data;
  }
}

const api = new BattleShipAPI();