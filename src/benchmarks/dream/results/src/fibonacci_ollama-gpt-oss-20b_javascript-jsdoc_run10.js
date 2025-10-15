/**
 * Returns the nth Fibonacci number.
 *
 * @param {number} n - The index (non‑negative integer).
 * @returns {number} The nth Fibonacci number.
 * @throws {Error} If `n` is negative or not an integer.
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

export default fibonacci;   // or: module.exports = fibonacci;
