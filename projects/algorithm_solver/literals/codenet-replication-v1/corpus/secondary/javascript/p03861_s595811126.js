function Main(input) {
  input = input.trim()
  var [a,b,c] = input.split(" ").map(BigInt);
  console.log(((b/c)-(a==0?0n:a-1n)/c+((a==0n)?1n:0n)).toString())
}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));
