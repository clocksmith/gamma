var inf = Number.MAX_SAFE_INTEGER;
function Main(input) {
	input = input.split("\n");
	var n = input[1]-0;
	var arr = input[0].split("");
	var ans = "";
	for(var i=0;i<arr.length;i++){
		if(i%n==0) ans += arr[i];
	}
	console.log(ans)
}Main(require("fs").readFileSync("/dev/stdin", "utf8").trim());