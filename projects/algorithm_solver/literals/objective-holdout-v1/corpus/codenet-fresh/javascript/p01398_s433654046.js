var objStr={};
var abc="abcdefghijklmnopqrstuvwxyz".split("");
abc.forEach(function(v,i){
   objStr[v]=i;
});
var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
while(true){
   var N=Arr.shift()-0;
   if(N==0)break;
   var str=Arr.shift();
   var AB=[];
   for(var i=0;i<N;i++){
      var ab=(Arr.shift()).split(" ").map(Number);
      AB.push(ab);
   }
   AB.reverse();
   var s=str.split("");
   for(var i=0;i<N;i++){
      var ab=AB[i];
      var a=ab[0]-1;
      var b=ab[1]-1;
      var plus=b-a;
      var A=s[a];
      var B=s[b];
      s[a]=abc[(objStr[B]+plus)%abc.length];
      s[b]=abc[(objStr[A]+plus)%abc.length];
   }
   console.log(s.join(""));
}