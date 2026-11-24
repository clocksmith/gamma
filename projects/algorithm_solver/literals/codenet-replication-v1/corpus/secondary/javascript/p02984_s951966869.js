function myout(text){console.log(text);}//standard output
function Main(input) {
	//input = parseInt(input);
	//input = input.split(" ");
	input = input.split("\n");
	//input = input.split(" ").map((a)=>Number(a));
	//input = input.split("\n").map((a)=>Number(a));
  var N = parseInt(input[0]);
  var list = input[1].split(" ").map((a)=>Number(a));
  var ruiseki = 0;
  for(var i = 0; i < list.length; i++){
    ruiseki += list[i];
  }
  var result = [];
  var tmp = 0;//x1を求めるとき用に偶数要素の累積を持たせる
  for(var i = 1; i < list.length; i = i + 2){
    tmp += list[i];
  }
  result[0] = ruiseki - 2 * tmp;
  for(var i = 1; i < list.length; i++){
    result.push(2 * list[i - 1] - result[i - 1]);
  }
  myout(result.join(" "));
}

Main(require("fs").readFileSync("/dev/stdin", "utf8").trim());
