var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
var n=Arr.shift()-0;
var arr=Arr.shift().split("");
var cnt=0;
for(var i=0;i<n;i++){
   var str=Arr.shift();
   var a="";
   for(var j=0;j<47;j++){
      var s=arr.join(a);
      if(s>=100)break;
      var re = new RegExp(s);
      if(re.test(str)){cnt++;break;}
      a+=".";
   }
}
console.log(cnt);