const input = require("fs").readFileSync("/dev/stdin", "utf8")

const lines = input.split('\n')
const X = lines[0] - 0

let five = [0, 1]

const max = X * X
for (let i = 2; five[five.length - 1] < max; i++) {
    five.push(Math.pow(i, 5))
}

;(() => {
    for (let i = 0; i < five.length; i++) {
        for (let j = 0; j < five.length; j++) {
            if (five[i] - five[j] === X) {
                console.log(i, j)
                return
            } else if (five[i] + five[j] === X) {
                console.log(i, -j)
                return
            }
        }
    }
})()