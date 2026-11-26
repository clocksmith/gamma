// inputに入力データ全体が入る
function Main(input) {
	// 1行目がinput[0], 2行目がinput[1], …に入る
	input = input.trim().split(" ").map((n) => parseInt(n));
	var N = input[0]
	var K = input[1]
	var S = input[2]
	var ans = ""
	for (var i = 1; i <= N; i++) {
		if (i <= K) {
			ans += S + " "	
		} else {
			if (S === 1) {
				ans += (S + 1) + " "
			} else {
				ans += (S - 1) + " "
			}
		}
	}
	ans.replace(/ $/, '')	

	//出力
	console.log(ans)
}
//*この行以降は編集しないでください（標準入出力から一度に読み込み、Mainを呼び出します）
Main(require("fs").readFileSync("/dev/stdin", "utf8"));
// Main(require('fs').readFileSync('./input.txt', 'utf-8'));