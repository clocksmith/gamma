process.stdin.resume();
process.stdin.setEncoding('utf8');

var lines = [];
var reader = require('readline').createInterface({
  input: process.stdin,
  output: process.stdout
});
reader.on('line', (line) => {
  lines.push(line);
});
reader.on('close', () => {
    const [Q, H, S, D] = lines[0].split(" ").map(v=>BigInt(v));
    const N = BigInt(lines[1]);
    if(N%2n==0n){
        const unit = min(Q*8n, H*4n, S*2n, D);
        log(N/2n*unit);
    }else{
        const unit1 = min(Q*4n, H*2n, S);
        const unit2 = D;
        if(unit1*2n < D){
            log(N*unit1);
        }else{
            log((N-1n)/2n * unit2 + unit1);
        }
    }
});

min = (...a) => {return a.reduce((a,b)=>a<b?a:b, a[0])}
log = (a)=>{console.log(a.toString())};
