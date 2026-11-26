var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var [a,n,m]=input.trim().split(" ").map(Number);
var cnt=0;
var i=1;
while(true){
   var k = Math.pow(i,n);
   if(k>m)break;
   var ary=(k+"").split("").map(Number);
   var sum = ary.reduce((a,b) => a+b);
   if(Math.pow(a+sum,n)==k)cnt++;
   i++;
}
console.log(cnt);
