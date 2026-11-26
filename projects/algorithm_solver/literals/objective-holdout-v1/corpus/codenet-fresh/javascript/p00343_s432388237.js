var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr=input.trim().split("\n");
var n=arr.shift()-0;
arr.forEach(v=>{
   var sente=v.split(" ").map(Number);
   var gote=[];
   for(var i=1;i<=13;i++)gote.push(i);
   gote=gote.filter(x=> !(x==7 || sente.includes(x)));
   var saiki=function(a,b,min,max,sg){
      if(a.length==0)return true;
      else if(b.length==0)return false;
      if(sg==0){
         var cnt=0;
         if(a.includes(min)){
            if(saiki(a.filter(v=> v!=min),b,min-1,max,1))cnt++;
         }
         if(a.includes(max)){
            if(saiki(a.filter(v=> v!=max),b,min,max+1,1))cnt++;
         }
         if(!a.includes(min) && !a.includes(max)){
            if(saiki(a,b,min,max,1))cnt++;
         }
         if(cnt==0)return false;
         else return true;
      }else if(sg==1){
         var cnt=0;
         if(b.includes(min)){
            if(!saiki(a,b.filter(v=> v!=min),min-1,max,0)) cnt++;
          }  
         if(b.includes(max)){
            if(!saiki(a,b.filter(v=> v!=max),min,max+1,0)) cnt++;
         }
         if(!b.includes(min) && !b.includes(max)){
            if(!saiki(a,b,min,max,0))cnt++;
         }
         if(cnt==0)return true;
         else return false;
      }
   };
   
   var flag = saiki(sente,gote,6,8,0,0);
   console.log(flag?"yes":"no");
});
