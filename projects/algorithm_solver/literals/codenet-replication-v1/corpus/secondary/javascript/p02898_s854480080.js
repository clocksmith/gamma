function Main(input) {
    input = input.split("\n");
    var N = input[0].split(" ")[0];
    var K = input[0].split(" ")[1];
    var h = input[1].split(" ");
    var res = 0;
    
    for(var i = 0; i < N; i++){
        h[i] = parseInt(h[i]);
        if(K <= h[i]){
            res++
        }
    }
    console.log(res);
}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));