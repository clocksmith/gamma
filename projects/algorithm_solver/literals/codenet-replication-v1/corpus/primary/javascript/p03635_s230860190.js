function Main(input) {
	tmp = input.split(" ");
	var n = tmp[0];
	var m = tmp[1];
	var a = n-1;
	var b = m-1;
	var c = a*b;
	console.log(c);
}
 
Main(require("fs").readFileSync("/dev/stdin", "utf8"));