export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  initialDelay: number = 1000
): Promise<T> {
  let attempt = 0;
  let delay = initialDelay;
  let lastError: unknown;

  while (attempt <= maxRetries) {
    try {
      return await fn();
    } catch (err) {
      lastError = err;
      if (attempt === maxRetries) break;
      await new Promise(res => setTimeout(res, delay));
      delay *= 2; // exponential backoff
    }
    attempt++;
  }

  throw lastError;
}
