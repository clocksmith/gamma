/**
 * Returns the nth Fibonacci number (0‑based).
 *
 * @param n - The index of the Fibonacci sequence (must be a non‑negative integer).
 * @returns The nth Fibonacci number.
 * @throws {RangeError} If `n` is negative or not an integer.
 */
export function fibonacci(n: number): number {
  if (!Number.isInteger(n) || n < 0) {
    throw new RangeError('n must be a non‑negative integer');
  }

  if (n === 0) return 0;
  if (n === 1) return 1;

  let a = 0,
      b = 1;

  for (let i = 2; i <= n; i++) {
    const next = a + b;
    a = b;
    b = next;
  }

  return b;
}
