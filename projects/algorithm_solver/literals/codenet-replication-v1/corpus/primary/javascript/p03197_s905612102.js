function myout(text){console.log(text);}//standard output
function Main(input) {
	//input = parseInt(input);
	//input = input.split(" ");
	//input = input.split("\n");
	//input = input.split(" ").map((a)=>Number(a));
	input = input.split("\n").map((a)=>Number(a));
  var N = input[0];
  input.shift();
  var output = "second";
  for(var i = 0; i < N; i++){
    if(input[i] % 2 == 1){
       output = "first";
      break;
    }
  }
  myout(output);
}

Main(require("fs").readFileSync("/dev/stdin", "utf8").trim());
