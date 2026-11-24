'use strict';
(function(stdin) {
    var inputs = stdin.toString().split(' ').map(Number);
    var a = inputs[0];
    var b = inputs[1];
    var d = Math.floor(a / b);
    var r = a % b;
    var f = Number((a / b).toFixed(5));
    console.log(d,r,f);
}(require('fs').readFileSync('/dev/stdin', 'utf8')));