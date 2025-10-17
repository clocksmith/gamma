export function fibonacci(n: number): number {
    if (!Number.isInteger(n) || n < 0) {
        throw new RangeError('n must be a non‑negative integer');
    }
    if (n === 0) return 0;
    if (n === 1) return 1;

    let a = 0;
    let b = 1;
    for (let i = 2; i <= n; i++) {
        const next = a + b;
        a = b;
        b = next;
    }
    return b;
}
