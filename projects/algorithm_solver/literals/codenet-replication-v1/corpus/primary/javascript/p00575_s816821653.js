let input = require('fs').readFileSync('/dev/stdin', 'utf8');
let [a,b,c] = input.trim().split(" ").map(Number);
let [d,sum] = [1,a];

while(1){
    if(c <= sum){
        console.log(d);
        break;
    }
    ++d;
    sum += a;
    if(d % 7 === 0){
        sum += b;
    }
}
