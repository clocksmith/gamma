// inputに入力データ全体が入る
function Main(input) {
	var line = input.split("\n");
	var N = Number(line[0]);
	var a = line[1].split(" ");
	var obj = {};
	for(var i = 0; i < a.length; i++){
		if(obj[a[i]]){
			obj[a[i]]++;
		} else{
			obj[a[i]] = 1;
		}
	}

	var ans = 0;

	for(var key in obj){
		if(Number(key) <= obj[key]){
			ans += obj[key] - Number(key);
		} else{
			ans += obj[key];
		}
	}

	console.log(ans);
}

//*この行以降は編集しないでください（標準入出力から一度に読み込み、Mainを呼び出します）
Main(require("fs").readFileSync("/dev/stdin", "utf8"));