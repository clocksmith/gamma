function Main(input) {
  const data = parseInt(input, 10);
  var sum = 0;
  for (var i = 1; i <= data; i++) {
    sum += i;
  }
  console.log(sum);
}
 
Main(require("fs").readFileSync("/dev/stdin", "utf8"));