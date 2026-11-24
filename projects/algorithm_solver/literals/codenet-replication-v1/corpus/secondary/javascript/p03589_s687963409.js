'use strict'
function Main(input){
  var N=input.trim()-0;
  var a=1,b=1;
  roop: while(true){
    for(b=a;b<=3500;b++){
      if(4*a*b-N*a-N*b>0&&(a*b*N)%(4*a*b-N*b-N*a)===0)
        break roop;
      }
    a++;
  }
  var c=Math.round(a*b*N/(4*a*b-N*a-N*b));
  console.log(a+' '+b+' '+c);
}

Main(require('fs').readFileSync('/dev/stdin','utf8'));