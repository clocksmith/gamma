export async function retryWithBackoff(asyncFn, maxAttempts = 3, initialDelay = 1000) {
  let attempt = 0;
  let delay = initialDelay;

  while (true) {
    try {
      return await asyncFn();
    } catch (err) {
      if (++attempt >= maxAttempts) throw err;
      await new Promise(res => setTimeout(res, delay));
      delay *= 2;
    }
  }
}
