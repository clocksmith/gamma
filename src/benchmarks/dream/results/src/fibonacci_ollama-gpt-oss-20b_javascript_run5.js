/**
 * Returns the nth Fibonacci number (0‑based).
 *
 * @param {number} n - The index of the Fibonacci number to compute.
 * @returns {number} The nth Fibonacci number.
 */
export function fibonacci(n) {
  if (n < 0) throw new Error('n must be a non‑negative integer');

  let a = 0, b = 1;
  if (n === 0) return a;
  if (n === 1) return b;

  for (let i = 2; i <= n; i++) {
    [a, b] = [b, a + b];
  }
  return b;
}
