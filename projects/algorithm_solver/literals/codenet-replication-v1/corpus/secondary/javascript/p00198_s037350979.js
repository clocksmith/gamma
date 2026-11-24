function move(d1,d2,d3,d4,d5,d6){
   var x=this.toString();
   if(x=="N")return [d2,d6,d3,d4,d1,d5];
   if(x=="E")return [d4,d2,d1,d6,d5,d3];
}
function roll(d1,d2,d3,d4,d5,d6){
   return [d1,d3,d5,d2,d4,d6];
}
function rolls(arr){
   for(var i=0;i<4;i++){
      obj[arr.join(",")]=true;
      arr=roll.apply(null,arr);
   }
}
var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.trim()).split("\n");
while(true){
   var n=Arr.shift()-0;
   if(n==0)break;
   var OBJ={};
   var result="Yes";
   var cnt=0;
   for(var i=0;i<n;i++){
      var obj={};
      var color="Red,Yellow,Blue,Magenta,Green,Cyan".split(",");
      var dice=(Arr.shift()).split(" ");
      dice=dice.map(function(v){return color.indexOf(v);});
      for(var j=0;j<4;j++){
         rolls(dice);
         dice=move.apply("N",dice);
      }
      dice=move.apply("E",dice);
      rolls(dice);
      dice=move.apply("E",dice);
      dice=move.apply("E",dice);
      rolls(dice);
      for(var k in obj){
         if(OBJ.hasOwnProperty(k)){cnt++;break;}
         else OBJ[k]=true;
      }
   }
   console.log(cnt);
}