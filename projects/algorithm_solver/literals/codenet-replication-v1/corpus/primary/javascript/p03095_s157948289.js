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
    var MOD = Math.pow(10,9)+7;

    var N = lines[0];
    var S = lines[1].split("");
    var result = 1;
    var alphabet = Array(26).fill(0);

    for (var i = 0; i < N; i++) {
        var tmp = S[i].charCodeAt() -97;
        alphabet[tmp]++;
    }

    for (var i = 0; i < 26; i++) {
        result = result * (alphabet[i] + 1);
        result = result % MOD;
    }
    console.log(result - 1);
});