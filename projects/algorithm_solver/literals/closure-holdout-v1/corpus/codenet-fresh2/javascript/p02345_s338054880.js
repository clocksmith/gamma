var MAX = Math.pow(2, 31) - 1;

var data = [];
function init(n) {
    for (var i = 0; i < n * 2 - 1; i++) data[i] = MAX;
}
function find(s, t, k, l, r) {
    if (r <= s || t <= l) return MAX;
    if (s <= l && r <= t) return data[k];

    var mid = Math.floor((l + r) / 2);
    var lv = find(s, t, k * 2 + 1, l, mid);
    var rv = find(s, t, k * 2 + 2, mid, r);

    return Math.min(lv, rv);
}

var input = require('fs').readFileSync('/dev/stdin', 'utf8').trim();
var lines = input.split('\n');

var items = lines.shift().trim().split(' ');
var n = +items[0];
var q = +items[1];

var m = 1;
while (m < n) m *= 2;

function update(i, x) {
    i += m - 1;
    data[i] = x;
    while (i > 0) {
        i = Math.floor((i - 1) / 2);
        var c1 = data[i * 2 + 1];
        var c2 = data[i * 2 + 2];
        data[i] = Math.min(c1, c2);
    }
}

init(m);

var line;
while (line = lines.shift()) {
    var com = line.trim().split(' ').map(function(n){return +n;});
    if (com[0] == 0) {
        update(com[1], com[2]);
    } else {
        console.log(find(com[1], com[2] + 1, 0, 0, m));
    }
}