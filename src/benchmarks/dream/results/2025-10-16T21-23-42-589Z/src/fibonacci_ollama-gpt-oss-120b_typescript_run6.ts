export function fibonacci(n: number): number {
    if (n < 0) throw new RangeError('n must be non‑negative');
    if (n === 0) return 0;
    if (n === 1) return 1;

    let a = 0, b = 1;
    for (let i = 2; i <= n; i++) {
        const next = a + b;
        a = b;
        b = next;
    }
    return b;
}
