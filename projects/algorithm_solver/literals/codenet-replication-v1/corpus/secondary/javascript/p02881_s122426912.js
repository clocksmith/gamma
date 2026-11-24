function Main(arg) {
 
    var N = arg.split("\n")[0];
    
    var ans = Number.MAX_SAFE_INTEGER;
    for (var i = 1; i <= Math.sqrt(N); i++){
        if (N % i === 0) {
            var tmp = (i - 1) + (N / i - 1);
            if (ans > tmp) {
                ans = tmp;
            }
        }
    }

    console.log(ans)

    return;
}

Main(require("fs").readFileSync("/dev/stdin", "utf8"));