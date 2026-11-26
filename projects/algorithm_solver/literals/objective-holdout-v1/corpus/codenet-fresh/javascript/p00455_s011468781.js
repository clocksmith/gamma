var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
Arr.forEach(function(v){
var arr=v.split(" ").map(Number);
var time=(arr[3]*3600+arr[4]*60+arr[5])-(arr[0]*3600+arr[1]*60+arr[2]);
var m=time%60;
var s=((time-m)%3600)/60;
var h=Math.floor(time/3600);
console.log(h+" "+s+" "+m);
});