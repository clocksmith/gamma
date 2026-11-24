var input = require('fs').readFileSync('/dev/stdin', 'utf8').trim();
var lines = input.split('\n');

var line;
while (line = lines.shift()) {
    var nums = line.split(' ');
    var n = +nums[0];
    var r = +nums[1];
    if (n + r == 0) break;

    var deck = [];
    for (var i = n; i > 0; i--) {
        deck.push(i);
    } 

    for (var i = 0; i < r; i++) {
        d = lines.shift().split(' ').map(function(n){return +n;});
        var p = d[0];
        var c = d[1];

        var top = deck.splice(p - 1, c);
        for (var j = 0; j < c; j++) {
            deck.unshift(top.pop());
        }
    }
        console.log(deck[0]);
}