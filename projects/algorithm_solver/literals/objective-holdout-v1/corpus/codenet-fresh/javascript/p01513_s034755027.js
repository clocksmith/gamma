var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
while(true){
   var n=Arr.shift()-0;
   if(n==0)break;
   var M=[];
   for(var i=0;i<n;i++){
      var m=(Arr.shift()).split(" ").map(Number);
      m.shift();
      M.push(m);
   }
   var K=(Arr.shift()).split(" ").map(Number);
   K.shift();
   var arr=[];
   M.forEach(function(m,i){
     var flag=K.every(function(k){return m.indexOf(k)!=-1;});
      if(flag)arr.push(i);
   });
   console.log((arr.length==1)?arr[0]+1:-1);
}