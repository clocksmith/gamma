/**
 * Returns the nth Fibonacci number (0‑based index).
 *
 * @param n - The position in the Fibonacci sequence (must be a non‑negative integer).
 * @returns The nth Fibonacci number.
 *
 * @throws {RangeError} If `n` is negative or not an integer.
 */
export function fibonacci(n: number): number {
  if (!Number.isInteger(n) || n < 0) {
    throw new RangeError('n must be a non‑negative integer');
  }

  // Base cases
  if (n === 0) return 0;
  if (n === 1) return 1;

  let a = 0,
      b = 1,
      c = 0;

  for (let i = 2; i <= n; i++) {
    c = a + b;
    a = b;
    b = c;
  }

  return c;
}
