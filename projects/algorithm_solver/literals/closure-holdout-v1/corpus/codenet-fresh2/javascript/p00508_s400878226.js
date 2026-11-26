var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr = input.trim().split("\n");
var n = arr.shift() - 0;
var a = arr.map(v => {
    return v.split(" ").map(Number);
});
a.sort(function(a, b) {
    return a[0] - b[0];
});
var min = Infinity;
for (var i = 0; i < a.length - 1; i++) {
    min = Math.min(min, Math.pow(a[i + 1][0] - a[i][0], 2) + Math.pow(a[i + 1][1] - a[i][1], 2));
}
for (var i = 0; i < a.length - 1; i++) {
    for (var j = i + 1; j < a.length; j++) {
        if (Math.pow(a[j][0] - a[i][0], 2) >= min) break;
        min = Math.min(min, Math.pow(a[j][0] - a[i][0], 2) + Math.pow(a[j][1] - a[i][1], 2));
    }
}
console.log(min);
