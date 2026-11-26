const main = input => {
  const grid = input.trim().split('\n')
  console.log(grid[0].charAt(0) + grid[1].charAt(1) + grid[2].charAt(2))
}
// 標準入力
main(require("fs").readFileSync("/dev/stdin", "utf8"))
