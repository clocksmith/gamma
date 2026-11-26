function main(input) {
  var temp = input.split('\n');
  var foo = temp[0].split(' ');
  var h = parseInt(foo[0]);
  var w = parseInt(foo[1]);

  temp.shift();
  var arr = [];
  for (var i = 0; i < h; i++) {
    arr[i] = temp[i].split(' ').map(Number);
  }
  var c = [];
  for (var j = 0; j < (temp.length - h - 1); j ++) {
    c.push(parseInt(temp[(j+h)]));
  }
  for (var k = 0; k < arr.length; k++) {
    var line = 0;
    for (var l = 0; l < w; l++) {
      line += arr[k][l]*c[l];
    }
    console.log(line);
  }  
}

var x = require('fs').readFileSync('/dev/stdin', 'utf-8');
main(x);
