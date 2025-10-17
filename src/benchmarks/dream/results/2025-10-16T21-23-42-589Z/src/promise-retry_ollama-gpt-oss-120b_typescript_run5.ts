export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  initialDelay: number = 1000
): Promise<T> {
  const delay = (ms: number) => new Promise(res => setTimeout(res, ms));

  let attempt = 0;
  let lastError: unknown;

  while (attempt <= maxRetries) {
    try {
      return await fn();
    } catch (err) {
      lastError = err;
      if (attempt === maxRetries) break;
      const backoff = initialDelay * 2 ** attempt;
      await delay(backoff);
      attempt++;
    }
  }

  throw lastError;
}
