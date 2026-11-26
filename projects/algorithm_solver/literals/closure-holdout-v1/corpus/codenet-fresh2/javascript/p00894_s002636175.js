var input = require('fs').readFileSync('/dev/stdin', 'utf8');
input=input.replace(/\/|\:/g," ").replace(/I/g,"1").replace(/O/g,"0");
var arr=input.trim().split("\n");
while(true){
   var n=arr.shift()-0;
   if(n==0)break;
   var obj={};
   var flag=false;
   while(n--){
      var MDhmep=arr.shift().split(" ").map(Number);
      (function(M,D,h,m,e,p){
         var time=M*30*24*60+D*24*60+h*60+m;
         if(p==0){
            if(e==1){
               flag=true;
               for(var k in obj){
                  if(obj[k][0]!=0)obj[k][0]=time;
               }
            }
            if(e==0){
               flag=false;
               for(var k in obj){
                  if(obj[k][0]!=0)obj[k][1]+=time-obj[k][0];
               }
            }
         }
         if(p!=0){
            if(!obj.hasOwnProperty(p))obj[p]=[0,0];
            if(e==1)obj[p][0]=time;
            if(e==0 && flag){
               obj[p][1]+=time-obj[p][0];
               obj[p][0]=0;
            }
            if(e==0 && !flag)obj[p][0]=0;
         }
      }).apply(null,MDhmep);
   }
   var max=0;
   for(var k in obj){
      if(obj[k][1]>max)max=obj[k][1];
   }
   console.log(max);
}