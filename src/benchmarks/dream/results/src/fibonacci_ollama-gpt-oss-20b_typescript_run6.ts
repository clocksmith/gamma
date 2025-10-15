/**
 * Returns the nth Fibonacci number (0‑indexed).
 *
 * @param n - A non‑negative integer.
 * @returns The Fibonacci number at position `n`.
 * @throws {Error} If `n` is negative.
 */
export function fibonacci(n: number): number {
  if (n < 0) {
    throw new Error('n must be a non‑negative integer');
  }

  if (n === 0) return 0;
  if (n === 1) return 1;

  let a = 0; // F(0)
  let b = 1; // F(1)

  for (let i = 2; i <= n; i++) {
    const next = a + b;
    a = b;
    b = next;
  }

  return b;
}
