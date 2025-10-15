/**
 * Return the nth Fibonacci number (0‑indexed).
 *
 * @param {number} n - The index of the Fibonacci number to compute.
 * @returns {number} The nth Fibonacci number.
 */
export function fibonacci(n) {
  if (n < 0) throw new Error('n must be non‑negative');

  let a = 0, b = 1;
  for (let i = 0; i < n; i++) {
    [a, b] = [b, a + b];
  }
  return a;
}
