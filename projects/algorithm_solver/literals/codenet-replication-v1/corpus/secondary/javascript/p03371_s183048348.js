function Main(input){
    input = input.split(" ");
    input = input.map(function(val){return parseInt(val, 10);});
    var priceA = input[0] < input[2] * 2 ? input[0] : input[2] * 2;
    var priceB = input[1] < input[2] * 2 ? input[1] : input[2] * 2;
    var sum = 0;
    
    if(input[0] + input[1] > input[2] * 2){
        var n = input[3] < input[4] ? input[3] : input[4];
        sum += n * 2 * input[2];
        input[3] -= n;
        input[4] -= n;
    }
    
    sum += input[3] * priceA;
    sum += input[4] * priceB;
    
    console.log(sum);
}    
Main(require("fs").readFileSync("/dev/stdin", "utf8"));