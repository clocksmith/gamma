var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.replace(/\n$/,"")).split("\n");
while(true){
   var n=Arr.shift()-0;
   if(n===0)break;
   var ans=[];
   for(var I=0;I<n;I++){
      var arr=(Arr.shift()).split(" ");
      var name=arr.shift()-0;
      arr=arr.map(Number);
      var score=[0,0,0,0,0,0,0,0,0,0];
      var bonus=[];
      var ab=0;
      var now=0;
      for(var i=0;i<arr.length;i++){ 
         var v=arr[i];
         score[now]+=v;
         if(bonus.indexOf("b1")!=-1)bonus[bonus.indexOf("b1")]=v;
         if(bonus.indexOf("b1")!=-1)bonus[bonus.indexOf("b1")]=v;
         if(bonus.indexOf("b2")!=-1)bonus[bonus.indexOf("b2")]="b1";      
         if(now==9)continue;
         if(v==10){
            if(ab==0){bonus.push("b1");bonus.push("b2");}
            if(ab==1)bonus.push("b1");
            now++;
            ab=0;
         }else if(ab==1){
            if(score[now]==10)bonus.push("b1");
            now++;
            ab=0;
         }else if(ab==0){
            ab=1;
         }
      }
      score=score.concat(bonus);
      var sum=score.reduce(function(a,b){return a+b;});
      ans.push([name,sum]);
   }
   ans.sort(function(a,b){
      if(a[1]==b[1])return a[0]-b[0];
      else return b[1]-a[1];
   });
   ans.forEach(function(v){console.log(v[0]+" "+v[1]);});
}