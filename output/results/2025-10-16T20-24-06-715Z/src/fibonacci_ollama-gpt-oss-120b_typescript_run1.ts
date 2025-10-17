export function fibonacci(n: number): number {
    if (n <= 0) return 0;
    let a = 0, b = 1;
    for (let i = 1; i < n; i++) {
        const temp = a + b;
        a = b;
        b = temp;
    }
    return b;
}
