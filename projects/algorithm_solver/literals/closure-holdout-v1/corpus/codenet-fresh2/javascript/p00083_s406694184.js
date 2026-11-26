function G(y,m,d){
   var date = new Date(m+"/"+d+"/"+y);
   return date.getTime();
}

var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");

Arr.forEach(function(v){
var arr=v.split(" ").map(Number);
var y=arr[0];
var m=arr[1];
var d=arr[2];
var time=G(y,m,d);
var str="";
if(time<G(1868,9,8))str="pre-meiji";
if(time>=G(1868,9,8))str="meiji "+(y-1868+1)+" "+m+" "+d;
if(time>=G(1912,7,30))str="taisho "+(y-1912+1)+" "+m+" "+d;
if(time>=G(1926,12,25))str="showa "+(y-1926+1)+" "+m+" "+d;
if(time>=G(1989,1,8))str="heisei "+(y-1989+1)+" "+m+" "+d;
console.log(str);
});