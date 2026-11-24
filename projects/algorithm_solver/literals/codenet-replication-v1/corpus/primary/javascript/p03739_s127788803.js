const input = require("fs").readFileSync("/dev/stdin", "utf8")

;(input => {

    const lines = input.split('\n')
    const N = lines[0] - 0
    const a = lines[1].split(' ').map(Number)

    let ans1 = 0
    let sum = 0
    for (let i = 0; i < N; i++) {
        const odd = i % 2
        if (!odd & sum + a[i] > 0) {
            sum += a[i]
        } else if (odd & sum + a[i] < 0) {
            sum += a[i]
        } else {
            ans1 += Math.abs(sum + a[i] - (odd ? -1 : 1))
            sum = odd ? -1 : 1
        }
    }

    let ans2 = 0
    sum = 0
    for (let i = 0; i < N; i++) {
        const odd = (i + 1) % 2
        if (!odd & sum + a[i] > 0) {
            sum += a[i]
        } else if (odd & sum + a[i] < 0) {
            sum += a[i]
        } else {
            ans2 += Math.abs(sum + a[i] - (odd ? -1 : 1))
            sum = odd ? -1 : 1
        }
    }

    console.log(Math.min(ans1, ans2))

})(input)
