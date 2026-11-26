var Main = input => {
    input = input.split("\n");
    tmp1 = input[0].split(" ");
    var N = parseInt(tmp1[0], 10);
    var D = parseInt(tmp1[1], 10);
    var X = [];
    for(var i = 0; i < N; i++) {
        X[i] = input[i + 1].split(" ");
    }

    var count = 0;
    for (var i = 0; i < N; i++) {
        for (var j = 0; j < N; j++) {
            if (i === j) {
                break;
            } else {
                var diff = [];
                var value = 0;
                for (var k = 0; k < D; k++) {
                    diff[k] = Math.pow(X[i][k] - X[j][k], 2);
                }
                value = Math.sqrt(diff.reduce((total, data) => {return total + data}));
                if (Number.isInteger(value)){count++;}
            }
        }
    }
    console.log(count);
}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));
