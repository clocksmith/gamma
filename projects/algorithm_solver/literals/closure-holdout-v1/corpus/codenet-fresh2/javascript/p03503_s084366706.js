process.stdin.resume();
process.stdin.setEncoding('utf8');

var g_input = '';
process.stdin.on('data', function(chunk) {
    g_input += chunk;
});

process.stdin.on('end', function() {
    Main(g_input.split(/\r?\n/));
});

function Main(input) {

    var n = parseInt(input[0], 10);
    var f = new Array(n);
    for (var i = 0; i < n; i++) {
        f[i] = new Array(10);
        var args = input[1 + i].split(' ');
        for (var j = 0; j < 10; j++) {
            f[i][j] = parseInt(args[j], 10);
        }
    }
    var p = new Array(n);
    for (var i = 0; i < n; i++) {
        p[i] = new Array(10);
        var args = input[1 + n + i].split(' ');
        for (var j = 0; j < 10; j++) {
            p[i][j] = parseInt(args[j], 10);
        }
    }

    var ret = Number.MIN_SAFE_INTEGER;
    for (var i = 1; i < 1024; i++) {
        var cc = 0;
        for (var j = 0; j < n; j++) {
            var c = 0;
            for (var k = 0; k < 10; k++) {
                if ((i >> k & 1) == 1 && f[j][k] > 0) {
                    c++;
                }
            }
            cc += p[j][c];
        }
        if (ret < cc) {
            ret = cc;
        }
    }

    console.log(ret);

    return 0;
}

