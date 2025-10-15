/**
 * Return the nth Fibonacci number (0‑based).
 *
 * @param {number} n - Non‑negative integer index.
 * @returns {number} The nth Fibonacci number.
 */
export function fibonacci(n) {
  if (n < 0 || !Number.isInteger(n)) {
    throw new TypeError('n must be a non‑negative integer');
  }

  if (n === 0) return 0;
  if (n === 1) return 1;

  let a = 0, b = 1;
  for (let i = 2; i <= n; i++) {
    [a, b] = [b, a + b];
  }
  return b;
}
