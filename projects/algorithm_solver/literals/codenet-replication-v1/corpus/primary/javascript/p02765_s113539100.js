function Main(input) {
		input = input.split(" ");
		const num = parseInt(input[0], 10);
		const rate = parseInt(input[1], 10);
		if(num > 10) {
				console.log(rate);
		} else {
				console.log(rate+(100 * (10 - num)));
		}
}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));