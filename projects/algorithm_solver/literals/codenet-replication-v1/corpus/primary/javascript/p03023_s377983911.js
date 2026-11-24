(function() {
function Main(input) {
  lines = input.split("\n")[0] * 1
  ans = (lines - 2) * 180
  console.log(ans);
}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));
}())
