export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  initialDelay: number = 1000
): Promise<T> {
  let attempt = 0;
  let delay = Math.max(0, initialDelay);

  while (true) {
    try {
      return await fn();
    } catch (error) {
      if (attempt >= maxRetries) throw error;
      await new Promise(res => setTimeout(res, delay));
      delay *= 2;
      attempt++;
    }
  }
}
