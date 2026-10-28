class LRUCache {
  constructor(capacity) {
    this.capacity = capacity;
    this.entries = new Map();
    this.first = {next: null, previous: null};
    this.last = {next: null, previous: this.first};
    this.first.next = this.last;
  }
  _remove(entry) {
    entry.previous.next = entry.next;
    entry.next.previous = entry.previous;
  }
  _append(entry) {
    entry.previous = this.last.previous;
    entry.next = this.last;
    this.last.previous.next = entry;
    this.last.previous = entry;
  }
  get(key) {
    const entry = this.entries.get(key);
    if (entry === undefined) return -1;
    this._remove(entry);
    this._append(entry);
    return entry.value;
  }
  put(key, value) {
    let entry = this.entries.get(key);
    if (entry === undefined) {
      entry = {key, value, previous: null, next: null};
      this.entries.set(key, entry);
    } else {
      entry.value = value;
      this._remove(entry);
    }
    this._append(entry);
    if (this.entries.size > this.capacity) {
      const oldest = this.first.next;
      this._remove(oldest);
      this.entries.delete(oldest.key);
    }
  }
}
module.exports = {LRUCache};
