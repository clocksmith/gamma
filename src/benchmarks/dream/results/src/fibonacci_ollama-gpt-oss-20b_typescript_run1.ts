/**
 * Returns the nth Fibonacci number (0‑based index).
 *
 * @param n - The index of the Fibonacci sequence (must be a non‑negative integer).
 * @returns The nth Fibonacci number.
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
    const next = a + b; // F(i) = F(i-1) + F(i-2)
    a = b;              // shift window
    b = next;
  }

  return b; // F(n)
}
