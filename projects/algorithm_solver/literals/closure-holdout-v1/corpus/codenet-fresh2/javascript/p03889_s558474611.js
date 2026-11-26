
function trans(c){
	if(c == "d")return "b"; 
	if(c == "b")return "d";
	if(c == "q")return "p";
	if(c == "p")return "q";
}

function Main(inputData) {
	init(inputData);
	
	var s = inS();

	for(var i = 0; i < s.length; i++){
		if(trans(s[i]) != s[s.length-i-1]){
			outln("No");
			return 0;
		} 
	}
	outln("Yes");
}


////////////////////////////////////////////////////////////////////////////////////
var input,inputCnt;

// "実行する"ボタンを押した時に実行される関数 (デバッグ用)
function debug(){
	Main(document.getElementById("input").value);
}

function init(inputData){
    //配列inputに順番に代入
	input = inputData.replace( /\n/g , " " );
	input = input.split(" ");
	inputCnt = 0;
}
//output
const out = (output) => { console.log(output) }
const outln = (output) => { console.log(output+"\n") }

//input
const inS = () => {return input[inputCnt++]};
const inI = () => {return parseInt(inS(), 10)};
const inF = () => {return parseFloat(inS())};

//*この行以降は編集しないでください（標準入出力から一度に読み込み、Mainを呼び出します）
Main(require("fs").readFileSync("/dev/stdin", "utf8"));
