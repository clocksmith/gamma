var lines = [];
var readline = require('readline');

var rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
});

rl.on('line', function (x) {
    lines.push(x);
});

rl.on('close', function () {
    var H = Number(lines[0].split(" ")[0]);
    var W = Number(lines[0].split(" ")[1]);
    lines.shift();

    var a = lines.map(i => i.split(" ").map(i => Number(i)));
    var ans = [];

    for (var i = 0; i < H - 1; i++) {
        for (var j = 0; j < W; j++) {
            if (a[i][j] % 2 !== 0) {
                a[i][j]--; a[i + 1][j]++;
                var str = (i + 1).toString() + " " + (j + 1).toString() + " " + (i + 2).toString() + " " + (j + 1).toString();
                ans.push(str)
            }
        }
    }

    for (var j = 0; j < W - 1; j++) {
        if (a[H - 1][j] % 2 !== 0) {
            a[H - 1][j]--; a[H - 1][j + 1]++;
            var str = H.toString() + " " + (j + 1).toString() + " " + H.toString() + " " + (j + 2).toString();
            ans.push(str)
        }
    }

    console.log(ans.length)
    for (var value of ans) { console.log(value); }
});