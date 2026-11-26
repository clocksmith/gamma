var input = require('fs').readFileSync('/dev/stdin', 'utf8');
var Arr=(input.slice(0,-1)).split("\n");
var obj={};
obj[" "]="101";
obj["'"]="000000";
obj[","]="000011";
obj["-"]="10010001";
obj["."]="010001";
obj["?"]="000001";
obj["A"]="100101";
obj["B"]="10011010";
obj["C"]="0101";
obj["D"]="0001";
obj["E"]="110";
obj["F"]="01001";
obj["G"]="10011011";
obj["H"]="010000";
obj["I"]="0111";
obj["J"]="10011000";
obj["K"]="0110";
obj["L"]="00100";
obj["M"]="10011001";
obj["N"]="10011110";
obj["O"]="00101";
obj["P"]="111";
obj["Q"]="10011111";
obj["R"]="1000";
obj["S"]="00110";
obj["T"]="00111";
obj["U"]="10011100";
obj["V"]="10011101";
obj["W"]="000010";
obj["X"]="10010010";
obj["Y"]="10010011";
obj["Z"]="10010000";

obj["00000"]="A";
obj["00001"]="B";
obj["00010"]="C";
obj["00011"]="D";
obj["00100"]="E";
obj["00101"]="F";
obj["00110"]="G";
obj["00111"]="H";
obj["01000"]="I";
obj["01001"]="J";
obj["01010"]="K";
obj["01011"]="L";
obj["01100"]="M";
obj["01101"]="N";
obj["01110"]="O";
obj["01111"]="P";
obj["10000"]="Q";
obj["10001"]="R";
obj["10010"]="S";
obj["10011"]="T";
obj["10100"]="U";
obj["10101"]="V";
obj["10110"]="W";
obj["10111"]="X";
obj["11000"]="Y";
obj["11001"]="Z";
obj["11010"]=" ";
obj["11011"]=".";
obj["11100"]=",";
obj["11101"]="-";
obj["11110"]="'";
obj["11111"]="?";

Arr.forEach(function(v){
   var arr=v.split("");
   var str="";
   for(var i=0;i<arr.length;i++){
      str+=obj[arr[i]];
   }
   while(str.length%5!=0){
      str+="0";
   }
   str=str.replace(/(.....)/g,function(s){
   return obj[s];
   });
   console.log(str);
});