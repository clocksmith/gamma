'use strict';
(function(stdin) {
  //declare function
  function firstTest(array) {
    if (array[0] < 0 || array[1] < 0) {
      return 'F';
    }
    var sum = array[0] + array[1];
    var border = [80, 65, 50, 30, 0];
    var grade = ['A', 'B', 'C', secondTest(array[2]), 'F'];
    for (var i = 0; i < 5; i++) {
      if (sum >= border[i]) {
        return grade[i];
      }
    }
  }

  function secondTest(x) {
    return x >= 50 ? 'C' : 'D';
  }

  //declare variable
  var inputs = stdin.toString().trim().split('\n');
  var clone = inputs.slice(0, inputs.indexOf('-1 -1 -1')).map(function(v) {
    return v.split(' ').map(Number);
  });
  //main
  //display
  console.log(clone.map(firstTest).join('\n'));
})(require('fs').readFileSync('/dev/stdin', 'utf8'));