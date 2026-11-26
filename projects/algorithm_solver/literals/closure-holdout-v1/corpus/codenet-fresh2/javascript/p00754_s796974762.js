var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
for(var i=0;i<Arr.length;i++){
   var str=Arr[i];
   if(str==".")break;
   str=str.replace(/[a-zA-Z]|\.|\s/g,"");
   while(str.match(/\[\]|\(\)/)){
      str=str.replace(/\[\]|\(\)/g,"");
   }
   console.log((str=="")?"yes":"no");
}