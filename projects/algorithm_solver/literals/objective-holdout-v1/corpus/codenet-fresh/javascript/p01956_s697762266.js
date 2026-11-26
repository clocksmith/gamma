var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr=input.trim().split("\n");
var [n,h,w]=arr.shift().split(" ").map(Number);
var x=arr.shift().split(" ").map(Number);
var m=[];
for(var i=0;i<(n*w);i++)m[i]=1;
x.forEach((v,i)=>{
   var k=(i%2==0)?w*i+v:w*i-v;
   for(var j=k;j<k+w;j++)m[j]=0;
});
var sum=m.reduce((a,b)=>a+b);
console.log(sum*h);
