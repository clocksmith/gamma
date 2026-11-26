function Main(input) {
    var firstLine = input[0].split(/\s/);
    var N = parseInt(firstLine[0], 10);
    var M = parseInt(firstLine[1], 10);
    var H = input[1].split(/\s/).map(h => parseInt(h, 10));
    var AB = input.slice(2).map(ab => {
        var s = ab.split(/\s/);
        return {
            A: s[0],
            B: s[1]
        };
    });
    var list = new Array(N);
    list.fill(true);

    for (var i = 0; i < M; i++) {
        list[AB[i].A - 1] = list[AB[i].A - 1] && H[AB[i].A - 1] > H[AB[i].B - 1];
        list[AB[i].B - 1] = list[AB[i].B - 1] && H[AB[i].B - 1] > H[AB[i].A - 1];
    }

    var result = 0;
    for (var i = 0; i < N; i++) {
        if (list[i]) {
            result++;
        }
    }

    console.log(result);
}

Main(require("fs").readFileSync("/dev/stdin", "utf8").trim().split(/\n/));