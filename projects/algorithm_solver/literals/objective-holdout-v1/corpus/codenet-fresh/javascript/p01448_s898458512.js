var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
var n=Arr.shift()-0;
var arr=[];
for(var i=0;i<=100001;i++)arr[i]=1;
for(var i=0;i<n;i++){
   var ab=(Arr.shift()).split(" ").map(Number);
   var a=ab[0];
   var b=ab[1];
   for(var j=a;j<=b;j++)arr[j]++;
}
var max=1;
for(var i=2;i<=100001;i++){
   if(arr[i]>=i)max=i;
}
console.log(max-1);