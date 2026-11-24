function Main(input) {
    input = input.trim().split("\n").map(function(x) { return x.split(" ")});
    let N = parseInt(input[0][0], 10);
    let K = parseInt(input[0][1], 10);
    let bitVec = Array.from({length:N}, () => true);
    let A = [];
    for (let i = 0; i < K; i++){
        A = input[2 * i + 2].map(e => parseInt(e, 10));
        for (x of A){
            bitVec[x - 1] = false;
        }
    }
    let ans = 0;
    for (let x of bitVec){
        if (x) ans++;
    }
    console.log(ans);
}

Main(require("fs").readFileSync("/dev/stdin", "utf8"));
