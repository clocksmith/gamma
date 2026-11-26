function main(input) {
  let N = parseInt(input, 10);
  let ans;
  
  if (N === 10 || N === 100 || N === 1000 || N === 10000 || N === 100000) {
  	console.log(10);
    return;
  }
  
  while(true) {
    if (!ans) { 
      ans = Math.floor(N % 10);
    } else {
      ans += Math.floor(N % 10);
    };
    
    N = N / 10;
    
    if (N <= 0) { break; }
  }
  
  console.log(ans);
}

main(require('fs').readFileSync('/dev/stdin', 'utf8'));