var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var str=input.trim();
var arr=[0];
if(/J/.test(str)==false)str="";
if(/O/.test(str)==false)str="";
if(/I/.test(str)==false)str="";
str.replace(/(J+)(O+)(I+)/g,function(s,s1,s2,s3){
   if(s1.length>=s2.length && s3.length>=s2.length)arr.push(s2.length);
   return "";
});
console.log(Math.max.apply(null,arr));