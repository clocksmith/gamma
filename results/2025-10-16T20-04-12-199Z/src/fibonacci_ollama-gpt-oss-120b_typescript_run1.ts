export function fibonacci(n: number): number {
    if (n < 0) throw new RangeError('n must be non‑negative');
    if (n === 0) return 0;
    let a = 0, b = 1;
    for (let i = 1; i < n; i++) {
        const tmp = a + b;
        a = b;
        b = tmp;
    }
    return b;
}
