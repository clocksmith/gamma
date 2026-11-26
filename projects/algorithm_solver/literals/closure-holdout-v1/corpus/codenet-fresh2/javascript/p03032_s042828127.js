var lines = [];

var readline = require("readline");
var rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
});

rl.on("line", function (x) {
    lines.push(x);
});

rl.on("close", function () {

    var N = Number(lines[0].split(" ")[0])
    var K = Number(lines[0].split(" ")[1])
    var V = lines[1].split(" ").map(i => Number(i))

    var result_l = [];
    var ans = 0;

   
    for (var left = 0; left <= Math.min(N, K); left++) {
        // leftが0の時、一個も宝石を取得しない
        if (1 <= left) { result_l.push(V[left - 1]) }
        var result_r = result_l.concat();

        for (var right = 0; left + right <= Math.min(N, K); right++) {
            // rightが0の時、一個も宝石を取得しない
            if (1 <= right) { result_r.push(V[V.length - 1 - right + 1]) }
            var result_t = result_r.concat();
            result_t.sort((a, b) => a - b);

            var trash = K - (left + right);
            for (var index = 0; index < trash; index++) {
                if (result_t[0] < 0) { result_t.shift() }
                else { break; }
            }

            var t = 0;
            for (var index = 0; index < result_t.length; index++) { t += result_t[index]; }
            ans = Math.max(ans, t)

            // console.log(left, right, trash, result_t, ans)
        }
    }
    console.log(ans);

});