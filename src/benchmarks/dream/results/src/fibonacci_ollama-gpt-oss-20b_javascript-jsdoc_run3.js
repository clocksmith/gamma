/**
 * Return the nth Fibonacci number (0‑indexed).
 *
 * @param {number} n - The index of the Fibonacci number to compute (n ≥ 0).
 * @returns {number} The nth Fibonacci number.
 */
export function fibonacci(n) {
  if (n < 0) throw new RangeError('n must be non‑negative');
  if (n === 0) return 0;
  if (n === 1) return 1;

  let a = 0, b = 1;
  for (let i = 2; i <= n; i++) {
    [a, b] = [b, a + b];
  }
  return b;
}
