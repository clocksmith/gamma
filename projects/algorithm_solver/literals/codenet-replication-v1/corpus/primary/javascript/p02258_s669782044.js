function main(input) {
  input = input.split("\n");

  var min = Number.MAX_VALUE, val = -Number.MAX_VALUE;
  var N = parseInt(input[0]);
  for (var i = 1; i <= N-1; i++) {
    if (min >= parseInt(input[i])) {
      min = parseInt(input[i]);
    }
    if (parseInt(input[i+1]) - min >= val) {
      val = parseInt(input[i+1]) - min;
    }
  }
  console.log(val);
  return val;
}
main(require("fs").readFileSync("/dev/stdin", "utf8"));