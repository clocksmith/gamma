export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  initialDelay: number = 1000
): Promise<T> {
  const sleep = (ms: number) => new Promise(res => setTimeout(res, ms));

  let attempt = 0;
  while (true) {
    try {
      return await fn();
    } catch (err) {
      if (attempt >= maxRetries) throw err;
      const delay = initialDelay * 2 ** attempt;
      await sleep(delay);
      attempt++;
    }
  }
}
