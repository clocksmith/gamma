function bomb(y,arr){
   if(y==Y){
      var sum=0;
      for(var i=0;i<X;i++){
         var cnt=0;
         for(var j=0;j<Y;j++){
            if(arr[j][i]==0)cnt++;
         }
         sum+=Math.max(cnt,Y-cnt);
      }
      max=Math.max(max,sum);
      return;
   }
   bomb(y+1,arr);
   if(y==-1)return;
   arr[y].forEach(function(v,i){arr[y][i]=1-v;});
   bomb(y+1,arr);
}
var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
while(true){
   var rc=Arr.shift().split(" ").map(Number);
   var Y=rc[0];
   var X=rc[1];
   if(Y==0 && X==0)break;   
   var yx=[];
   for(var i=0;i<Y;i++){
      var v=Arr.shift().split(" ").map(Number);
      yx.push(v);
   }
   var max=0;
   bomb(-1,yx);
   console.log(max);
}