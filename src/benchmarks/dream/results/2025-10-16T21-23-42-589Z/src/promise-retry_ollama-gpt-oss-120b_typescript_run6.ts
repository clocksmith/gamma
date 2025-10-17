export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  initialDelay: number = 1000
): Promise<T> {
  const wait = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

  let attempt = 0;
  while (true) {
    try {
      return await fn();
    } catch (err) {
      if (attempt >= maxRetries) {
        throw err;
      }
      const delay = initialDelay * 2 ** attempt;
      await wait(delay);
      attempt++;
    }
  }
}
