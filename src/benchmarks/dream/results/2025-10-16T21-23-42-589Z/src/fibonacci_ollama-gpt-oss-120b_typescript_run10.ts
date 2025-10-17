export function fibonacci(n: number): number {
    if (n < 0) throw new Error('n must be non‑negative');

    let a = 0, b = 1;
    for (let i = 0; i < n; i++) {
        [a, b] = [b, a + b];
    }
    return a;
}
