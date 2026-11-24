function Main(input) {
	var output = 0;
  if(input.length <= 2){
     console.log(output);
    return;
     }
  input = input.replace(/BC/g,"D");//BCは塊なので1文字へ 
  var renzoku = 0;
  for(var i = 0; i < input.length; i++){
    var tmp = input.slice(i , i + 1);
    if(tmp == "A"){
       renzoku++;
    }else if(tmp == "D"){
       output += renzoku;
    }else{
       renzoku = 0;
    }
  }
  
  console.log(output);
}

Main(require("fs").readFileSync("/dev/stdin", "utf8"));
