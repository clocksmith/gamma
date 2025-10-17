export async function retryWithBackoff(fn, maxAttempts = 3, delay = 1000) {
  let attempts = 0;
  let currentDelay = delay;

  while (true) {
    try {
      return await fn();
    } catch (err) {
      if (++attempts >= maxAttempts) throw err;
      await new Promise(res => setTimeout(res, currentDelay));
      currentDelay *= 2;
    }
  }
}
