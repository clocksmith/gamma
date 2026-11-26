process.stdin.resume();
process.stdin.setEncoding('utf8');

var g_input = '';
process.stdin.on('data', function(chunk) {
    g_input += chunk;
});

process.stdin.on('end', function() {
    Main(g_input.split(/\r?\n/));
});

function dfs(depth, last, used, r, d) {
    if (depth > r.length) {
        return 0;
    }
    var minDist = Number.MAX_VALUE;
    var dist = 0;
    for (var i = 0; i < r.length; i++) {
        if (used[i]) {
            continue;
        }
        used[i] = true;
        if (last >= 0) {
            dist = d[r[last] - 1][r[i] - 1];
        }
        minDist = Math.min(minDist, dfs(depth + 1, i, used, r, d) + dist);
        used[i] = false;
    }

    return minDist;
}

function Main(input) {
    var values = input[0].split(' ');
    var n = parseInt(values[0], 10);
    var m = parseInt(values[1], 10);
    var rNum = parseInt(values[2], 10);
    var r = new Array(rNum);
    var rStr = input[1].split(' ');
    for (var i = 0; i < rNum; i++) {
        r[i] = parseInt(rStr[i], 10);
    }
    var d = new Array(n);
    for (var i = 0; i < n; i++) {
        d[i] = new Array(n);
    }
    for (var i = 0; i < n; i++) {
        for (var j = 0; j < n; j++) {
            if (i == j) {
                d[i][j] = 0;
            }
            else {
                d[i][j] = Number.MAX_VALUE;
            }
        }
    }
    for (var i = 0; i < m; i++) {
        var distValues = input[i + 2].split(' ');
        var a = parseInt(distValues[0], 10);
        var b = parseInt(distValues[1], 10);
        var c = parseInt(distValues[2], 10);
        d[a - 1][b - 1] = c;
        d[b - 1][a - 1] = c;
    }
   
    for (var k = 0; k < n; k++) {
        for (var i = 0; i < n; i++) {
            for (var j = 0; j < n; j++) {
                if (d[i][j] > d[i][k] + d[k][j]) {
                    d[i][j] = d[i][k] + d[k][j];
                }
            }
        }
    }
    var used = new Array(rNum);
    for (var i = 0; i < rNum; i++) {
        used[i] = false;
    }
    var ans = dfs(1, -1, used, r, d);

    console.log(ans);

    return 0;
}

