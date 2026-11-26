var abc=[];
for(var i=0;i<=1111;i++)abc[i]=Math.pow(i,3);
var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr=input.trim().split("\n");
while(true){
   var z=arr.shift()-0;
   if(z==0)break;
   var ans=Infinity;
   for(var i=z-1;i>0;i--){
      for(var j=i;j>0;j--){
         var x=abc[z]-abc[i]-abc[j];
         if(x>0 && ans>x)ans=x;
      }
   }
   console.log(ans);
}