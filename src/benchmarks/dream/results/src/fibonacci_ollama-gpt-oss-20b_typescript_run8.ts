/**
 * Returns the nth Fibonacci number.
 *
 * @param n - The index (0‑based) of the Fibonacci sequence.
 * @returns The nth Fibonacci number.
 *
 * @example
 * fibonacci(0); // 0
 * fibonacci(1); // 1
 * fibonacci(5); // 5
 */
export function fibonacci(n: number): number {
  if (n < 0) {
    throw new Error('n must be a non‑negative integer');
  }

  if (n === 0) return 0;
  if (n === 1) return 1;

  let a = 0,
      b = 1;

  for (let i = 2; i <= n; i++) {
    const next = a + b;
    a = b;
    b = next;
  }

  return b;
}
