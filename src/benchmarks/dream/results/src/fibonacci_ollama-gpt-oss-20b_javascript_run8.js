/**
 * Return the nth Fibonacci number (0‑based).
 * F(0) = 0, F(1) = 1, F(n) = F(n‑1) + F(n‑2)
 *
 * @param {number} n - non‑negative integer
 * @returns {number}
 */
export function fibonacci(n) {
  if (n < 0) throw new Error('n must be non‑negative');
  if (n === 0) return 0;
  if (n === 1) return 1;

  let a = 0, b = 1;
  for (let i = 2; i <= n; i++) {
    [a, b] = [b, a + b];
  }
  return b;
}
