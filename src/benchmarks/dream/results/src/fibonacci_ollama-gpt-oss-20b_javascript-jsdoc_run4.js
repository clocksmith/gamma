/**
 * Return the nth Fibonacci number.
 *
 * @param {number} n - The index (0‑based) of the Fibonacci sequence.
 * @returns {number} The nth Fibonacci number.
 */
export function fibonacci(n) {
  if (n < 0) throw new Error('n must be a non‑negative integer');

  let a = 0, b = 1;
  for (let i = 0; i < n; i++) {
    [a, b] = [b, a + b];
  }
  return a;
}
