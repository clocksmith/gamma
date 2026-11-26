function Main(input) {
    input = input.trim().split("\n").map(function(x) { return x.split(" ")});    
    var N = parseInt(input[0][0], 10);
    var W = parseInt(input[0][1], 10);
    var arr_vw = [];
    var arr_dp = [Array.from({length: W + 1}, () => 0)];
    var tmpW;
    for (var i = 0; i < N; i++){
        arr_vw.push(input[i + 1].map(e => parseInt(e, 10)));
        arr_dp.push([]);
        tmpVw = arr_vw[i];
        for (var j = 0; j <= W; j++){
            if (j < tmpVw[1]) arr_dp[i + 1].push(arr_dp[i][j]);
            if (j >= tmpVw[1]){
                arr_dp[i + 1].push(Math.max(arr_dp[i][j], arr_dp[i + 1][j - tmpVw[1]] + tmpVw[0]));
            }
        }
    }
    console.log(arr_dp[N][W]);
}

Main(require("fs").readFileSync("/dev/stdin", "utf8")); 
