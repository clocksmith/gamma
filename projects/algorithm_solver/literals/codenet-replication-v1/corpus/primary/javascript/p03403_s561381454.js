function myout(text){console.log(text);}//standard output
function Main(input) {
	input = input.trim();
	//input = input.trim().split(" ");
	input = input.trim().split("\n");
	//input = input.trim().split(" ").map((a)=>Number(a));
	//input = input.trim().split("\n").map((a)=>Number(a));
  var len = parseInt(input[0]);
  var list = input[1].split(" ").map((a)=>Number(a));
  var sum = Math.abs(list[0]);
  for(var i = 0; i < len - 1; i++){
    sum += Math.abs(list[i] - list[i + 1]);
  }
  sum += Math.abs(list[len - 1]);
  
  //console.log("sum:" + sum);
  for(var i = 0; i < len; i++){
    var tmp = 0;
    if(i == 0){
       tmp = sum - Math.abs(list[0]) - Math.abs(list[0] - list[1]) + Math.abs(list[1]);
    }else if(i == list.length - 1){
      var last =  list.length - 1;
      tmp = sum - Math.abs(list[last - 1] - list[last]) - Math.abs(list[last]) + Math.abs(list[last - 1]);
    }else{
      tmp = sum - Math.abs(list[i-1] - list[i]) - Math.abs(list[i] - list[i+1]) + Math.abs(list[i-1] - list[i+1]);
    }
    console.log(tmp);
  }
  
}

Main(require("fs").readFileSync("/dev/stdin", "utf8"));
