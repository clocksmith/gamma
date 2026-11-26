var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr=input.trim().split("\n").map(Number);
while(true){
   var n=arr.shift();
   if(n==0)break;
   var k=arr.shift();
   var card=[];
   for(var i=0;i<n;i++)card.push(arr.shift());
   var all=[];
   var loop=function(ary){
      if(ary.length==k)all.push(ary);
      else{
         for(var i=0;i<n;i++){
            if(ary.indexOf(i)==-1)loop(ary.concat(i));
         }
      }
   };
   loop([]);
   var obj={};
   all.forEach(function(v){
      var str="";
      v.forEach(function(value){
         str+=card[value];
      });
      obj[str]=true;
   });
   console.log(Object.keys(obj).length);
}