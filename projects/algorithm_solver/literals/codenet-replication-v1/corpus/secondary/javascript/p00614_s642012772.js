var oturi=[];
for(var i=0;i<=500;i++){
   var sum=i;
   var cnt=0;
   while(sum>=500){sum-=500;cnt++;}
   while(sum>=100){sum-=100;cnt++;}
   while(sum>=50){sum-=50;cnt++;}
   while(sum>=10){sum-=10;cnt++;}
   while(sum>=5){sum-=5;cnt++;}
   while(sum>=1){sum-=1;cnt++;}
   oturi[i]=cnt;
}

var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr=input.trim().split("\n");
while(true){
   var str=arr.shift();
   if(str=="0 0 0 0 0 0 0")break;
   var ary=str.split(" ").map(Number);
   var P=ary[0];
   var min=Infinity;
   for(var i=P;i<P+500;i++){
      (function(p,a,b,c,d,e,f){
         var sum=i;
         var cnt=0;
         while(sum>=500 && f>0){sum-=500;f--;cnt++;}
         while(sum>=100 && e>0){sum-=100;e--;cnt++;}
         while(sum>=50 && d>0){sum-=50;d--;cnt++;}
         while(sum>=10 && c>0){sum-=10;c--;cnt++;}
         while(sum>=5 && b>0){sum-=5;b--;cnt++;}
         while(sum>=1 && a>0){sum-=1;a--;cnt++;}
         if(sum==0)min=Math.min(cnt+oturi[i-P],min);
      }).apply(null,ary);
   }
   console.log(min);
}