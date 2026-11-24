var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr=input.trim().split("\n");
while(true){
   var n=arr.shift()-0;
   if(n==0)break;
   var wh=arr.shift()-0;
   var obj=[];
   var ary=[];
   for(var i=0;i<n;i++){
      var data=arr.shift().split(" ");
      var name=data[0];
      var link=data[1]-0;
      obj[name]=[];
      if(i==0)ary.push(name);
      for(var j=0;j<link;j++)obj[name].push(arr.shift().split(" "));
   }
   var m=arr.shift()-0;
   var now=0;
   while(m--){
      var M=arr.shift().split(" ");
      if(M[0]=="show")console.log(ary[now]);
      else if(M[0]=="back"){
         now=Math.max(0,now-1);
      }else if(M[0]=="forward"){
         now=Math.min(now+1,ary.length-1);
      }else if(M[0]=="click"){
         var X=M[1]-0;
         var Y=M[2]-0;
         obj[ary[now]].forEach(function(v){
            var x1=v[0]-0;
            var y1=v[1]-0;
            var x2=v[2]-0;
            var y2=v[3]-0;
            if(x1<=X && X<=x2 && y1<=Y && Y<=y2){
               ary.length=now+1;
               ary.push(v[4]);
               now=ary.length-1;
            }
         });
      }
   }
}