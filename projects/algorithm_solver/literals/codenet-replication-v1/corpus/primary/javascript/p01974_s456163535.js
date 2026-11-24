var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr = input.trim().split("\n");
arr=arr.map(v=>v.split(" ").map(Number));
var n=arr.shift() - 0;
var a = arr.shift();
var k=n-1;
var flag=false;
for(var i=0;i<a.length;i++){
   for(var j=i+1;j<a.length;j++){
      if(Math.abs(a[i]-a[j])%k==0){
         console.log(a[i] + " " + a[j]);
         flag = true;
         break;
      }
   }
    if(flag)break;
}
