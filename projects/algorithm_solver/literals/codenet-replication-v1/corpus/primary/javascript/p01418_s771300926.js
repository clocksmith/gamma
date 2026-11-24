process.stdin.resume();
process.stdin.setEncoding("utf8");
process.stdin.on("data", function (chunk) {
    var input = chunk.trim().split(/\s+/).map(Number);

    var k = input[0];
    var l = input[1];
    var r = input[2];
    p = input[3];
    e = input[4];
    t = input[5];

    console.log(solve(k, r, l).toFixed(6));
});

var p, e, t;

function solve(k, r, l) {
    var h = (r + l) / 2.0;

    if (k == 0) {
        if (Math.abs(t - h) < e)
            return 1.0;
        else
            return 0.0;
    }

    if (r < t - e || t + e < l)
        return 0.0;
    else if (t - e <= l && r <= t + e)
        return 1.0;

    if (h <= t)
        return p * solve(k - 1, h, l) + (1.0 - p) * solve(k - 1, r, h);
    else
        return p * solve(k - 1, r, h) + (1.0 - p) * solve(k - 1, h, l);
}