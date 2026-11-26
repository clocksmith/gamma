const main = stdin => {
  const input = stdin.trim().split('\n')

  const [N, M, X, Y] = input[0].split(' ').map(x => parseInt(x))

  const xs = input[1].split(' ').map(x => parseInt(x))
  const ys = input[2].split(' ').map(x => parseInt(x))

  let xMax = -99999
  for (let i = 0; i < N; i++) {
    if (xs[i] > X && xs[i] > xMax) {
      xMax = xs[i]
    }
  }

  let yMin = 99999
  for (let i = 0; i < N; i++) {
    if (ys[i] <= Y && ys[i] <= yMin) {
      yMin = ys[i]
    }
  }

  if (xMax !== -99999 && yMin !== 99999 && xMax < yMin) {
    console.log('No War')
  } else {
    console.log('War')
  }
}


// 標準入力
main(require("fs").readFileSync("/dev/stdin", "utf8"))
