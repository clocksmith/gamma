var main = function(input) {
var Ar = input.split(' ').map(x=>parseInt(x));
var N=Ar[0];
var M=Ar[1];
var K=Ar[2];
var Ans ='No';
for (var i = 0; i <= N; i++) {
        for (var j = 0; j <= M; j++) {
            if (j * (N - i) + i * (M - j) == K) {
                Ans = 'Yes'
                console.log(Ans);
                return 0;
            }
        }
    }
console.log(Ans);
    return 0; 
}

main(require("fs").readFileSync("/dev/stdin", "utf8").trim());