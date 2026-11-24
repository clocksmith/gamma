var input = require('fs').readFileSync('/dev/stdin', 'utf8').trim();
var numbers = input.split("\n");
var min = 0;
var max = 9;


numbers.forEach(function(number) {
  var combinations = 0;
  for(var i = min; i <= max; i++) {
    for(var j = min; j <= max; j++) {
      for(var k = min; k <= max; k++) {
        for(var l = min; l <= max; l++) {
          if(i + j + k + l === parseInt(number, 10)) {
            combinations++;
          }
        }
      }
    }
  }
  console.log(combinations);
});