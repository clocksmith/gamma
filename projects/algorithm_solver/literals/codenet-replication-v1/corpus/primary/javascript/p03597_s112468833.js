function Main(input){
  var inp = input.split('\n');
  var N = parseInt(inp[0].trim());
  var A = parseInt(inp[1].trim());

  console.log( N * N - A);
}
Main(require('fs').readFileSync('/dev/stdin', 'utf8'));