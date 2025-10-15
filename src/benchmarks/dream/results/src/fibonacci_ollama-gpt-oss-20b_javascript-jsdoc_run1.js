/**
 * Returns the nth Fibonacci number.
 *
 * @param {number} n - The position in the Fibonacci sequence (non‑negative integer).
 * @returns {number} The nth Fibonacci number.
 */
function fibonacci(n) {
  if (!Number.isInteger(n) || n < 0) {
    throw new Error('n must be a non‑negative integer');
  }

  if (n === 0) return 0;
  if (n === 1) return 1;

  let a = 0, b = 1;
  for (let i = 2; i <= n; i++) {
    [a, b] = [b, a + b];
  }
  return b;
}

export { fibonacci };   // or: module.exports = fibonacci;
