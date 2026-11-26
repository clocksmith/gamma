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
    var N = Number(lines.shift());
    var b = Array(N + 1);

    var tmp = lines[0].split(" ");
    b[0] = -1;
    for (var i = 0; i < N; i++) {
        b[i + 1] = Number(tmp[i]);
    }

    var result = [];

    for (var i = 1; i <= N; i++) {
        var max = -1;
        for (var j = 1; j <= b.length; j++) {
            if (b[j] === j) { max = j; }
        }
        if (max !== -1) {
            result.push(b.splice(max, 1));
        }
        else {
            console.log("-1");
            return (0);
        }
    }
    for (var i = 0; i < N; i++) {
        console.log(Number(result.pop()));
    }
});