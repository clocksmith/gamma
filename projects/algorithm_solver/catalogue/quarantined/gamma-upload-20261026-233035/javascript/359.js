'use strict';
// 359. Logger Rate Limiter.
class Logger {
  constructor() { this.nextAllowed = new Map(); }
  shouldPrintMessage(timestamp, message) {
    if (timestamp < (this.nextAllowed.get(message) || 0)) return false;
    this.nextAllowed.set(message, timestamp + 10);
    return true;
  }
}
function solve(calls) {
  const logger = new Logger();
  return calls.map(call => logger.shouldPrintMessage(...call));
}
if (typeof module !== 'undefined') module.exports = { solve, Logger };
