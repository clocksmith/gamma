var input = require('fs').readFileSync('/dev/stdin', 'utf8').trim();
var lines = input.split('\n');

var line;
while (line = lines.shift()) {
    var nums = line.split(' ');
    var n = +nums[0];
    var m = +nums[1];
    if (n + m == 0) break;

    var p = [];
    for (var i = 0; i < n; i++) {
        p.push(i + 1);
    }

    while (p.length > 1) {
        for (var i = 0; i < m - 1; i++) {
            p.push(p.shift());
        }
        p.shift();
    }
    console.log(p[0]);
}