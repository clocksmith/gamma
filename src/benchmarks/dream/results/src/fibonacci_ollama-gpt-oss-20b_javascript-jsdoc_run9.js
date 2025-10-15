/**
 * Computes the nth Fibonacci number (0‑based indexing).
 *
 * @param {number} n - The index of the Fibonacci number to compute.
 * @returns {number} The nth Fibonacci number.
 * @throws {TypeError} If `n` is not a non‑negative integer.
 */
export function fibonacci(n) {
  if (typeof n !== 'number' || !Number.isInteger(n) || n < 0) {
    throw new TypeError('n must be a non‑negative integer');
  }

  if (n === 0) return 0;
  if (n === 1) return 1;

  let a = 0,
      b = 1;

  for (let i = 2; i <= n; i++) {
    [a, b] = [b, a + b];
  }

  return b;
}
