var main = function main(input) {
  var count = 0
  for (var i = 0; i < input.length; i++) {
      if (input[i] === 'o') count++ 
  }
  console.log(700 + count*100)
}
 
main(require('fs').readFileSync('/dev/stdin', 'utf-8'))
