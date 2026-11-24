var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr=input.trim().split("\n");
while(true){
   var N=arr.shift()-0;
   if(N==0)break;
   var f="";
   for(var I=0;I<N+1;I++){
      var n=arr.shift()-0;
      var ary=[];
      while(n--)ary.push(arr.shift().split(" ").map(Number));
      var r=[];
      for(var i=1;i<ary.length;i++){
         var a=ary[i-1];
         var b=ary[i];
         if(a[0]==b[0] && a[1]>b[1])r.push(["s",a[1]-b[1]]);
         else if(a[0]==b[0] && a[1]<b[1])r.push(["n",b[1]-a[1]]);
         else if(a[1]==b[1] && a[0]>b[0])r.push(["w",a[0]-b[0]]);
         else if(a[1]==b[1] && a[0]<b[0])r.push(["e",b[0]-a[0]]);
      }
      var rA=r.join("");
      var rB=r.reverse().join("");
      if(I==0){
         f=r.join("").replace(/n/g,"N").replace(/e/g,"E").replace(/s/g,"S").replace(/w/g,"W");
      }else{
         var NrA=rA.replace(/n/g,"N").replace(/e/g,"E").replace(/s/g,"S").replace(/w/g,"W");
         var ErA=rA.replace(/n/g,"E").replace(/e/g,"S").replace(/s/g,"W").replace(/w/g,"N");
         var SrA=rA.replace(/n/g,"S").replace(/e/g,"W").replace(/s/g,"N").replace(/w/g,"E");
         var WrA=rA.replace(/n/g,"W").replace(/e/g,"N").replace(/s/g,"E").replace(/w/g,"S");
         var NrB=rB.replace(/n/g,"N").replace(/e/g,"E").replace(/s/g,"S").replace(/w/g,"W");
         var ErB=rB.replace(/n/g,"E").replace(/e/g,"S").replace(/s/g,"W").replace(/w/g,"N");
         var SrB=rB.replace(/n/g,"S").replace(/e/g,"W").replace(/s/g,"N").replace(/w/g,"E");
         var WrB=rB.replace(/n/g,"W").replace(/e/g,"N").replace(/s/g,"E").replace(/w/g,"S");
         if(f==ErA || f==SrA || f==WrA || f==NrA || f==ErB || f==SrB || f==WrB || f==NrB)console.log(I);
      }
   }
   console.log("+++++");
}