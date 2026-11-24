function part1(a,b,c){
   var cnt=0;
   while(true){
      var flag=cnt;
      if(a>=1 && b>=1 && c>=1){a--;b--;c--;cnt++;}
      if(a>=3){a-=3;cnt++;}
      if(b>=3){b-=3;cnt++;}
      if(c>=3){c-=3;cnt++;}
      if(flag==cnt)break;
   }
   return cnt;
}
function part2(a,b,c){
   var cnt=0;
   while(true){
      var flag=cnt;
      if(a>=1 && b>=1 && c>=1){a--;b--;c--;cnt++;}
      if(a>=1 && b>=1 && c>=1){a--;b--;c--;cnt++;}
      if(a>=3){a-=3;cnt++;}
      if(b>=3){b-=3;cnt++;}
      if(c>=3){c-=3;cnt++;}
      if(flag==cnt)break;
   }
   return cnt;
}
function part3(a,b,c){
   var cnt=0;
   while(true){
      var flag=cnt;
      if(a>=3){a-=3;cnt++;}
      if(b>=3){b-=3;cnt++;}
      if(c>=3){c-=3;cnt++;}
      if(a>=1 && b>=1 && c>=1){a--;b--;c--;cnt++;}
      if(flag==cnt)break;
   }
   return cnt;
}
var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr=input.trim().split("\n");
while(true){
   var str=arr.shift();
   if(str=="0 0 0 0 0 0")break;
   var ary=str.split(" ").map(Number);
   var a=ary[0]+ary[3];
   var b=ary[1]+ary[4];
   var c=ary[2]+ary[5];
   var cnt=0;
   var A=(a-(a%3))/3;
   var B=(b-(b%3))/3;
   var C=(c-(c%3))/3;
   if(A>=1){A--;a=a%3+3;}
   if(B>=1){B--;b=b%3+3;}
   if(C>=1){C--;c=c%3+3;}
   cnt+=A+B+C;
   cnt+=Math.max(part1(a,b,c),part2(a,b,c),part3(a,b,c));
   console.log(cnt);
}