var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr=input.trim().split("\n");
while(true){
   var abc=arr.shift();
   if(abc=="0 0 0 0 0")break;
   var ary=(abc+" "+arr.shift()).split(" ").map(Number);
   (function(a,b,c,d,e,na,nb,nc){
      var A,B;
      var amari=nc%d;
      A=na*a+nb*b+Math.floor(nc/d)*d*e+amari*c;
      if(nc>=d)B=na*a+nb*b+nc*e;
      if(nc<d){
         var husoku=d-amari;
         while(husoku--){
            if(nb>0)nb--;
            else if(na>0)na--;
         }
         B=na*a+nb*b+d*e;
      }
      console.log(Math.min(A,B));
   }).apply(null,ary);
}