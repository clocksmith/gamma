function Main(input) {
	input = input.split(' ')
	const [A, B, C, K] = input.map(i => parseInt(i))

    if (A >= K) {
        console.log(K)
    } else if (A + B >= K) {
        console.log(A)
    } else {
        const pos = A
        const neg = K - (A + B)

        console.log(pos - neg)
    }
}
//*この行以降は編集しないでください（標準入出力から一度に読み込み、Mainを呼び出します）
Main(require("fs").readFileSync("/dev/stdin", "utf8"))