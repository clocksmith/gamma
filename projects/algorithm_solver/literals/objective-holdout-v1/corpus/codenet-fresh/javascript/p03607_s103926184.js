const input = require("fs").readFileSync("/dev/stdin", "utf8")

;(input => {

    const lines = input.split('\n')
    const N = lines[0] - 0

    const A = {}
    for (let i = 0; i < N; i++) {
        if (A[lines[i + 1]]) {
            A[lines[i + 1]] = 0
        } else {
            A[lines[i + 1]] = 1
        }
    }

    let count = 0
    for (let i in A) {
        count += A[i]
    }

    console.log(count)

})(input)
