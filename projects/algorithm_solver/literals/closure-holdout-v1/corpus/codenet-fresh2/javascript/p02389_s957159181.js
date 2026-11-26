'use strict';
(function(stdin) {
  var inputs = stdin.toString().trim().split('\n');
  var params = inputs[0].split(' ').map(Number);

  (function(a, b) {
    console.log(a*b, 2*(a + b));

  })(params[0], params[1]);

}(require('fs').readFileSync('/dev/stdin', 'utf8')));