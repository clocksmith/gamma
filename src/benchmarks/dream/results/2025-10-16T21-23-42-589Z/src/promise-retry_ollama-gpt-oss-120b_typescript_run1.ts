export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  initialDelay: number = 1000
): Promise<T> {
  const wait = (ms: number) => new Promise(res => setTimeout(res, ms));

  let attempt = 0;
  let delay = initialDelay;

  while (true) {
    try {
      return await fn();
    } catch (err) {
      if (attempt >= maxRetries) {
        throw err;
      }
      await wait(delay);
      delay *= 2; // exponential backoff
      attempt++;
    }
  }
}
