export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  initialDelay: number = 1000
): Promise<T> {
  const sleep = (ms: number) => new Promise(res => setTimeout(res, ms));

  let attempt = 0;
  let delay = initialDelay;
  let lastError: unknown;

  while (attempt <= maxRetries) {
    try {
      return await fn();
    } catch (err) {
      lastError = err;
      if (attempt === maxRetries) break;
      await sleep(delay);
      delay *= 2; // exponential backoff
    }
    attempt++;
  }

  throw lastError;
}
