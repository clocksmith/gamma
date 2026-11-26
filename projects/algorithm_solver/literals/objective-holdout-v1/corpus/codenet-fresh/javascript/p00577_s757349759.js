var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr= input.trim().split("\n");
var str = arr[1];
var cnt=0;
str.replace(/OX|XO/g,function(s){
   cnt++;
   return "";
});
console.log(cnt);
