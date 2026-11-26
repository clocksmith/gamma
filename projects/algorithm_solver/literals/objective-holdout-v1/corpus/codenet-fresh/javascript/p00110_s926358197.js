function bigAdd(x,y){
   var a=(x+"").split("").reverse().map(Number);
   var b=(y+"").split("").reverse().map(Number);
   var c=[];
   var max=Math.max(a.length,b.length);
   for(var i=0;i<max+1;i++)c[i]=0;
   for(var i=0;i<max;i++){
      var sum=0;
      if(a.length>i)sum+=a[i];
      if(b.length>i)sum+=b[i];
      c[i]+=sum;
   }
   for(var i=0;i<max;i++){
      if(c[i]>=10){
         c[i]-=10;
         c[i+1]++;
      }
   }
   if(c[c.length-1]==0)c.pop();
   var str=c.reverse().join("");
   return str;
}
var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=input.trim().split("\n");
while(true){
   if(Arr.length==0)break;
   var arr=Arr.shift().split(/[\+\=]/);
   var ans=[];
   for(var i=0;i<=9;i++){
      var a=arr[0].replace(/X/g,i);
      var b=arr[1].replace(/X/g,i);
      var c=arr[2].replace(/X/g,i);
      if(bigAdd(a,b)==c)ans.push(i);
   }
   console.log((ans.length==1)?ans[0]:"NA");
}