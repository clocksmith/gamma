var card={};
var a="123,234,345,456,567,678,789,111,222,333,444,555,666,777,888,999".split(",");
for(var i=0;i<a.length;i++){
   for(var j=0;j<a.length;j++){
      for(var k=0;k<a.length;k++){
         card[a[i]+a[j]+a[k]]=true;
         card[(a[i]+a[j]).split("").map(Number).sort(function(a,b){return a-b;}).join("")+a[k]]=true;
         card[a[k]+(a[i]+a[j]).split("").map(Number).sort(function(a,b){return a-b;}).join("")]=true;
         card[(a[i]+a[j]+a[k]).split("").map(Number).sort(function(a,b){return a-b;}).join("")]=true;
      }
   }
}
var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr=input.trim().split("\n");
var t=arr.shift()-0;
for(var i=0;i<t;i++){
   var n=arr.shift().split(" ").map(Number);
   var c=arr.shift().split(" ");
   var rgb={R:[],G:[],B:[]};
   c.forEach(function(v,i){
      rgb[v].push(n[i]);
   });
   var str="";
   for(var k in rgb){
      rgb[k].sort(function(a,b){return a-b;});
      if(rgb[k].length==3)str+=rgb[k].join("");
      else if(rgb[k].length==6)str+=rgb[k].join("");
      else if(rgb[k].length==9)str+=rgb[k].join("");
   }
   console.log((card.hasOwnProperty(str))?1:0);
}