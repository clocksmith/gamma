export const Toast = {
  container: null,

  init() {
    this.container = document.createElement('div');
    this.container.style.cssText = 'position: fixed; bottom: 20px; right: 20px; display: flex; flex-direction: column; gap: 10px; z-index: 1000;';
    document.body.appendChild(this.container);
  },

  show(message, type = 'info') {
    if (!this.container) this.init();
    
    const el = document.createElement('div');
    el.className = `achievement-toast ${type}`;
    el.innerHTML = `
      <div class="achievement-icon">★</div>
      <div>
        <div class="achievement-name">${message.name || 'Notification'}</div>
        <div class="achievement-desc">${message.desc || message}</div>
      </div>
    `;
    
    this.container.appendChild(el);
    setTimeout(() => {
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 300);
    }, 4000);
  }
};