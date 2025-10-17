async function retryWithBackoff(fn, maxAttempts = 3, initialDelay = 1000) {
  let attempt = 0;
  let delay = initialDelay;
  while (true) {
    try {
      return await fn();
    } catch (err) {
      if (++attempt > maxAttempts) throw err;
      await new Promise(r => setTimeout(r, delay));
      delay *= 2;
    }
  }
}

module.exports = retryWithBackoff;
