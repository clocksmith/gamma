var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var str=(input.trim()).replace(/egg/g,"E").replace(/chicken/g,"C");
while(/EE/.test(str))str=str.replace(/EE/,"EAE");
while(/CC/.test(str))str=str.replace(/CC/,"CAC");
var ary=str.split("A");
var ans="";
ary.forEach(function(v){
   if(ans.length<v.length)ans=v;
});
console.log((ans.slice(-1)=="E")?"egg":"chicken");