function main(input) {
  var args = input.split('\n');
  var N = parseInt(args[0],10);
  var H = parseInt(args[1],10);
  var W = parseInt(args[2],10);
  var h = N - H + 1;
  var w = N - W + 1;
  console.log(h * w);
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));