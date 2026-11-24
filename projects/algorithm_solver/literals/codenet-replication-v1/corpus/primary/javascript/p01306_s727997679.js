var dict={};
    dict["yotta"] = 24;
    dict["zetta"] = 21;
    dict["exa"] = 18;
    dict["peta"] = 15;
    dict["tera"] = 12;
    dict["giga"] = 9;
    dict["mega"] = 6;
    dict["kilo"] = 3;
    dict["hecto"] = 2;
    dict["deca"] = 1;
    dict["deci"] = -1;
    dict["centi"] = -2;
    dict["milli"] = -3;
    dict["micro"] = -6;
    dict["nano"] = -9;
    dict["pico"] = -12;
    dict["femto"] = -15;
    dict["ato"] = -18;
    dict["zepto"] = -21;
    dict["yocto"] = -24;
var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var arr=input.trim().split("\n");
var n=arr.shift()-0;
while(n--){
   var ary=arr.shift().split(" ");
   var a=ary[0].split("");
   var str="";
   var flag=true;
   a.forEach(function(v){
      if(v!="0" && v!="." && flag){str+=v+"#";flag=false;}
      else str+=v;
   });
   a=str.split("");
   var cnt=0;
   var one=0;
   var k;
   a.forEach(function(v){
      if(v=="." && one==0){k=-1;one=1;}
      else if(v=="#" && one==0){k=1;one=1;}
      else if(one==1 && v!="." && v!="#")cnt++;
      else if(one==1 && (v=="." || v=="#") )one=2;
   });
   var plus=(ary.length==3)?dict[ary[1]]:0;
   var b="10^"+(cnt*k+plus);
   var ans=a.join("").replace(/\./,"").replace(/#/g,".");
   ans=ans.replace(/^0+/,"");
   ans=ans.replace(/\.$/,"");
   console.log(ans+" * "+b+" "+ary[ary.length-1]);
}