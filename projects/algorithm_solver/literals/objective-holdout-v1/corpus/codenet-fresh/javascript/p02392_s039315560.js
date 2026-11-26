'use strict';
(function(stdin) {

    var inputs = stdin.toString().trim().split(' ');

    var a = Number(inputs[0]);
    var b = Number(inputs[1]);
    var c = Number(inputs[2]);
    if (a < b && b < c) {
        console.log('Yes');

    } else {
        console.log('No');
    }

}(require('fs').readFileSync('/dev/stdin', 'utf8')));