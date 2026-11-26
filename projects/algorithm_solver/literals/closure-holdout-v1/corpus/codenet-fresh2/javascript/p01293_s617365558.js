var input = require('fs').readFileSync('/dev/stdin', 'utf8');
input=input.replace(/([2-9])/g,"$1,");
input=input.replace(/T/g,"10,").replace(/J/g,"11,").replace(/Q/g,"12,").replace(/K/g,"13,").replace(/A/g,"14,");
var arr=input.trim().split("\n");
while(true){
   var str=arr.shift();
   if(str=="#")break;
   var n=arr.shift().split(" ");
   var e=arr.shift().split(" ");
   var s=arr.shift().split(" ");
   var w=arr.shift().split(" ");
   var first=0;
   var ns=0;
   var ew=0;
   for(var i=0;i<13;i++){
      var card=[];
      card[0]=n[i].split(",");
      card[1]=e[i].split(",");
      card[2]=s[i].split(",");
      card[3]=w[i].split(",");
      var r=card[first][1];
      var plus=(r==str)?15:0;
      var score=(card[first][0]-0)+plus;
      card.forEach(function(v,index){
         var plus=(v[1]==str)?15:0;
         if(r==v[1] || str==v[1]){
            if(score<=(v[0]-0)+plus){
               first=index;
               score=(v[0]-0)+plus;
            }  
         }
      });
      if(first==0 || first==2)ns++;
      else ew++;
   }
   var ans=(ns>ew)?"NS "+(ns-6):"EW "+(ew-6);
   console.log(ans);
}