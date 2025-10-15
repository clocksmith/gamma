/**
 * Returns the nth Fibonacci number (0‑based index).
 *
 * @param n - The position in the Fibonacci sequence (0 → 0, 1 → 1, 2 → 1, …).
 * @returns The nth Fibonacci number.
 * @throws {RangeError} If `n` is negative.
 */
export function fibonacci(n: number): number {
  if (!Number.isInteger(n)) {
    throw new TypeError('n must be an integer');
  }
  if (n < 0) {
    throw new RangeError('n must be non‑negative');
  }

  // Base cases
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
