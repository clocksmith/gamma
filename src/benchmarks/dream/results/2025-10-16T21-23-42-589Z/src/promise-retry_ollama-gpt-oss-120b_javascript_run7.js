export async function retryWithBackoff(fn, maxAttempts = 3, initialDelay = 1000) {
  let attempt = 0;
  let delay = initialDelay;
  while (true) {
    try {
      return await fn();
    } catch (e) {
      if (++attempt >= maxAttempts) throw e;
      await new Promise(r => setTimeout(r, delay));
      delay *= 2;
    }
  }
}
