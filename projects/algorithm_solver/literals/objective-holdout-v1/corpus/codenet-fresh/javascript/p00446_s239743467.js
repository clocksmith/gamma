var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n").map(Number);
while(true){
   var n=Arr.shift();
   if(n==0)break;
   var AB=[[],[]];
   for(var i=0;i<n;i++){
      var v=Arr.shift();
      AB[0].push(v);
   }
   AB[0].sort(function(a,b){return a-b;});
   for(var i=1;i<=n*2;i++){
      if(AB[0].indexOf(i)==-1)AB[1].push(i);
   }
   var now=0;
   var x=0;
   while(true){
      var one=0;
         AB[x]=AB[x].filter(function(v,index){
            if(v>now && one==0){one=1;now=v;return false;}
            else {return true;}
         });
      if(AB[x].length==0)break;
      if(one==0)now=0;
      x=1-x;
      }
      console.log(AB[1].length);
      console.log(AB[0].length);
}