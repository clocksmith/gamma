/**
 * Returns the nth Fibonacci number (0‑based).
 *
 * @param {number} n - The index (non‑negative integer).
 * @returns {number} The nth Fibonacci number.
 */
export function fibonacci(n) {
  if (n < 0) throw new Error('n must be a non‑negative integer');

  // Handle the first two numbers directly
  if (n === 0) return 0;
  if (n === 1) return 1;

  let a = 0, b = 1;
  for (let i = 2; i <= n; i++) {
    [a, b] = [b, a + b];
  }
  return b;
}
