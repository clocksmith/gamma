/**
 * Returns the nth Fibonacci number.
 *
 * @param n - The index (0‑based) of the Fibonacci sequence.
 * @returns The nth Fibonacci number.
 *
 * @throws {RangeError} If `n` is negative.
 */
export function fibonacci(n: number): number {
  if (n < 0) {
    throw new RangeError('n must be a non‑negative integer');
  }

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
