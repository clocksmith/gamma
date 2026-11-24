var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
var AL=Arr.shift();
var hash={};
for(var i=0;i<AL;i++){
   var arr=Arr[i].split(" ");
   var a=arr[0];
   if(!hash.hasOwnProperty(a))hash[a]=0;
   hash[a]+=arr[1]-0;
}
var X=[];
for(var i in hash)X.push(i);
X.sort();
var Max=0;
for(var i=0;i<X.length;i++)if(Max<=X[i].length)Max=X[i].length;
var Y=[];
for(var i=1;i<=Max;i++){
   var F=X.filter(function(v){return v.length==i;});
   Y=Y.concat(F);
}
for(var i=0;i<Y.length;i++)console.log(Y[i]+" "+hash[Y[i]]);