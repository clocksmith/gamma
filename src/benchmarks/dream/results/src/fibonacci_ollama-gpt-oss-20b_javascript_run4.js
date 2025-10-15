/**
 * Returns the nth Fibonacci number (0‑indexed).
 *
 * @param {number} n - The index of the Fibonacci number to compute.
 * @returns {number} The nth Fibonacci number.
 */
export function fibonacci(n) {
  if (n <= 0) return 0;          // F(0) = 0
  if (n === 1) return 1;         // F(1) = 1

  let a = 0, b = 1;              // F(0), F(1)
  for (let i = 2; i <= n; i++) {
    [a, b] = [b, a + b];         // iterate to F(i)
  }
  return b;
}


module.exports = fibonacci;
