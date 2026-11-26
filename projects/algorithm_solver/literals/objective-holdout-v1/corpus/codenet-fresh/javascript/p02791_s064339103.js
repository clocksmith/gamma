function Main(input) {
    var N = parseInt(input[0], 10);
    var P = input[1].split(/\s/).map(p => parseInt(p, 10))

    var min = P[0];
    var result = 0;

    for (var i = 0; i < N; i++) {
        if (min >= P[i]) {
            result++;
            min = P[i];
        }
    }

    console.log(result);
}

Main(require("fs").readFileSync("/dev/stdin", "utf8").trim().split(/\n/));