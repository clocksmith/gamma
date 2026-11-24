// inputに入力データ全体が入る
function Main(input) {
	var line = input.split("\n");
	var tmp = line[0].split(" ");
	var N = Number(tmp[0]);
	var M = Number(tmp[1]);
	var ans = Math.abs((M-2)*(N-2));
	if(ans > 1000000000000000){
		var MM = M-2;
		var NN = N-2;
		var MMtop = Math.floor(MM/10000);
		var MMbottom = MM%10000;
		var NNtop = Math.floor(NN/10000);
		var NNbottom = NN%10000;
		var MN1 = MMtop * NNtop;
		var MN2 = MMbottom * NNtop + NNbottom * MMtop;
		var MN3 = MMbottom * NNbottom;
		var MNbottom = (MN2 + Math.floor(MN3/10000)) + "";
		MNbottom += ("00000" + MN3%10000).slice(-4);
		var ans = (MN1 + Math.floor(Number(MNbottom)/100000000)) + "";
		ans += ("000000000" + MNbottom%100000000).slice(-8);
	}
	console.log(ans);
}

//*この行以降は編集しないでください（標準入出力から一度に読み込み、Mainを呼び出します）
Main(require("fs").readFileSync("/dev/stdin", "utf8"));