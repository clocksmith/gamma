function Main(input) {
	input = input.trim().split("\n").map(function(x) { return x.split(" ")});    
	let N = parseInt(input[0][0], 10);
	let ans = N + 1;
	for (let d = 1; d < N - 1; d++){
		ans += (N - d) * (d + 1);
		// console.log(ans);
		if (ans >= Number.MAX_SAFE_INTEGER) console.log("caution!");
	}
	let line, tmp1, tmp2;
	for (let i = 0; i < N - 1; i++){
		// console.log(ans);
		line = input[i + 1].map(e => parseInt(e, 10));
		if (line[1] < line[0]) line = [line[1], line[0]];
		tmp1 = Math.min(N - line[1], line[0] - 1) + 1;
		tmp2 = N - (line[1] - line[0]) - 1;
		ans -= ((tmp1 * tmp1) + tmp1 * (tmp2 - 2 * tmp1 + 2) - 1);
		// console.log(line);
		// console.log(tmp1, tmp2, (tmp1 * tmp1) + tmp1 * (tmp2 - 2 * tmp1 + 2) - 1);
	}
	if (N === 1) ans = 1;
	console.log(ans);
}

Main(require("fs").readFileSync("/dev/stdin", "utf8"));
