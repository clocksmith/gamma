function prime(max){
   var arr=[];
   for(var i=0;i<=max;i++)arr[i]=i;
   arr[0]=false;
   arr[1]=false;
   var sqrt=Math.floor(Math.sqrt(max));
   for(var i=2;i<=sqrt;i++){
      if(arr[i]==false)continue;
         for(var j=i+i;j<=max;j+=i){
            arr[j]=false;
         }
   }
   var result=[];
   for(var i=0;i<=max;i++){
      if(arr[i]!==false)result.push(arr[i]);
   }
   return result;
}
var pr=prime(1000000);

var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
for(var I=0;I<Arr.length;I++){
   var np=Arr[I].split(" ").map(Number);
   var n=np[0];
   var p=np[1];
   if(n==-1 && p==-1)break;
   var arr=[];
   for(var i=0;i<pr.length;i++){
      if(pr[i]>n){
         arr.push(pr[i]);
         if(arr.length>=50)break;
      }
   }
   var s=[];
   var obj={};
   for(var i=0;i<arr.length;i++){
      for(var j=0;j<arr.length;j++){
         if(obj.hasOwnProperty(j+" "+i))continue;
         obj[i+" "+j]=true;
         s.push(arr[i]+arr[j]);
      }
   }
   s.sort(function(a,b){return a-b;});
   console.log(s[p-1]);
}