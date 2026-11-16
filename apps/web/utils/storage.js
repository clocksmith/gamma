const DB_NAME = 'gamma_db';
const DB_VERSION = 1;

export const Storage = {
  db: null,

  async init() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);
      
      request.onupgradeneeded = (e) => {
        const db = e.target.result;
        if (!db.objectStoreNames.contains('sessions')) {
          db.createObjectStore('sessions', { keyPath: 'id', autoIncrement: true });
        }
        if (!db.objectStoreNames.contains('settings')) {
          db.createObjectStore('settings', { keyPath: 'key' });
        }
      };

      request.onsuccess = (e) => {
        this.db = e.target.result;
        resolve();
      };
      
      request.onerror = (e) => reject(e);
    });
  },

  async saveSession(sessionData) {
    return this._tx('sessions', 'readwrite', store => store.add(sessionData));
  },

  async getSessions() {
    return this._tx('sessions', 'readonly', store => store.getAll());
  },

  async saveSetting(key, value) {
    return this._tx('settings', 'readwrite', store => store.put({ key, value }));
  },

  async getSetting(key, defaultValue) {
    try {
      const result = await this._tx('settings', 'readonly', store => store.get(key));
      return result ? result.value : defaultValue;
    } catch {
      return defaultValue;
    }
  },

  _tx(storeName, mode, callback) {
    return new Promise((resolve, reject) => {
      const tx = this.db.transaction(storeName, mode);
      const store = tx.objectStore(storeName);
      const request = callback(store);
      
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }
};