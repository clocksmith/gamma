class MinStack {
  constructor() { this.head = null; }
  push(value) {
    this.head = {value, minimum: this.head === null ? value : Math.min(value, this.head.minimum), next: this.head};
  }
  pop() { this.head = this.head.next; }
  top() { return this.head.value; }
  getMin() { return this.head.minimum; }
}
module.exports = {MinStack};
