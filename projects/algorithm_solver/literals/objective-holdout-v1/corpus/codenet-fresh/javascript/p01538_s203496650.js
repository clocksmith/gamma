var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n").map(Number);
var N=Arr.shift()-0;
for(var I=0;I<N;I++){
   var v=Arr[I]-0;
   var obj={};
   obj[v]=true;
   var cnt=0;
   while(true){
      if(v<10)break;
      var str=v+"";
      var max=[];
      for(var i=1;i<str.length;i++){
         var a=parseInt(str.slice(0,i),10);
         var b=parseInt(str.slice(i),10);
         max.push(a*b);
      }
      v=Math.max.apply(null,max);
      if(obj.hasOwnProperty(v)){
         cnt=-1;
         break;
      }
      obj[v]=true;
      cnt++;
   }
   console.log(cnt);
}