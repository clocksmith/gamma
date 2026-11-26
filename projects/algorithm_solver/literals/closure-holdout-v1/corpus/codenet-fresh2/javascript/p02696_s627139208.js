function main(input) {
  let a,b,n;
  [a, b, n] = input[0].trim().split(" ").map(i => parseInt(i));

  
  let max = -100000000;
  if(n>=b){
    max = Math.floor(a*(b-1)/b) - (a * Math.floor((b-1)/b));
  }else{
    max = Math.floor(a*n/b) - (a * Math.floor(n/b));
  }
  console.log(max);
}
main(require('fs').readFileSync('/dev/stdin', 'utf8').trim().split("\n"));