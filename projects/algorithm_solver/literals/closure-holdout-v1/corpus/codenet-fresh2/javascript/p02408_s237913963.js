'use strict';
(function(stdin) {
  //declare function

  //declare variable
  function search(array) {
    return allCards.filter(function(card) {
      return array.indexOf(card) === -1;
    });
  }
  var inputs = stdin.toString().trim().split('\n');
  var line = [].concat(inputs);
  var make13 = [];
  for (var i = 0; i < 13; i++) {
    make13.push(i + 1);
  }
  var allCards = ['S', 'H', 'C', 'D'].map(function(v) {
    return [].concat(make13).map(function(w) {
      return [v, parseInt(w)].join(' ');
    });
  }).reduce(function(a, b) {
    return a.concat(b);
  });
  //main

  //display
  if (inputs[0] < 52) {
    console.log(search(line).join('\n'));
  }
})(require('fs').readFileSync('/dev/stdin', 'utf8'));