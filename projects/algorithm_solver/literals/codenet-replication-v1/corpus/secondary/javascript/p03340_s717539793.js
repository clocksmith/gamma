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
    var astr = input[1].split(' ');
    var a = new Array(n);

    for (var i = 0; i < n; i++) {
        a[i] = parseInt(astr[i], 10);
    }

    var ans = 0;
    var or = a[0];
    for (var l = 0, r = 0; l < n; l++) {

        while ((r + 1) < n && (or & a[r + 1]) === 0) {
            or |= a[r + 1];
            r++;
        }
        ans += r - l + 1;

        or &= ~a[l];
    }

    console.log(ans);

    return 0;
}
