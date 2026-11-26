var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr=input.trim().split("\n");
var index=-1;
while(true){
   var n=arr[++index]-0;
   if(n==0)break;
   var stone=[];
   while(n--)stone.push(arr[++index]-0);
   var ary=[];
   var flag=false;
   stone.forEach(function(v,i){
      flag=!flag;
      if(flag)ary.push(v);
      else {
         if(ary[ary.length-1]==v)ary.push(v);
         else{
            ary.push(v);
            i--;
            while(true){
               if(i<0 || ary[i]==v)break;
               else {
                  ary[i]=v;
                  i--;
               }
            }
         }
      }
   });
   var cnt=0;
   ary.forEach(function(v){
      if(v==0)cnt++;
   });
   console.log(cnt);
}