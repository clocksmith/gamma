var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr=input.trim().split("\n");
while(true){
   var m=arr.shift()-0;
   if(m==0)break;
   var xy=[];
   while(m--)xy.push(arr.shift().split(" ").map(Number));
   var obj={};
   var n=arr.shift()-0;
   while(n--){
      var ary=arr.shift().split(" ").map(Number);
      obj[ary[0]+","+ary[1]]=[ary[0],ary[1]];
   }
   for(var k in obj){
      var dx=obj[k][0]-xy[0][0];
      var dy=obj[k][1]-xy[0][1];
      var flag=xy.every(function(v){
         return (obj.hasOwnProperty((v[0]+dx)+","+(v[1]+dy)));
      });
      if(flag){console.log(dx,dy);break;}
   }
}