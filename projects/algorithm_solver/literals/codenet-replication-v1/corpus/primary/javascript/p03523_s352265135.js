function Main(input){
	var n = input.match(/^A?KIHA?BA?RA?$/);
	console.log(n==null?"NO":"YES");
}Main(require("fs").readFileSync("/dev/stdin", "utf8").trim());
