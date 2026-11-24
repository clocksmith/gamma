function Main(input) {
	input = input.split("\n");
	tmp = input[0].split(" ");
	
	var d = parseInt(tmp[0], 10);
	var t = parseInt(tmp[1], 10);
	var s = parseInt(tmp[2], 10);
	
	if  (d / s > t) {
	var result = "No";
	} else {
	var result = "Yes";
	}
	
	console.log(result);
	}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));