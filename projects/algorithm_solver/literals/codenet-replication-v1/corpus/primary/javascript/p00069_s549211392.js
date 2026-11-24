//設定値
var input = {};

//2次元長方形配列。 要素は-1(横棒の右側),0,1(横棒の左側)
var data = [];

//経路取得
var f = function(startLine, startStep){
	if(!startStep) startStep = 0;
	var now = startLine;
	var result = [now];
	for(var y=startStep; y<data.length; y++){
		now += data[y][now];
		result.push(now);
	}
	return result;
};
//ゴール指定時の経路取得 (経路はスタートから)
var rf = function(endLine){
	var now = endLine;
	var result = [now];
	for(var y=data.length-1; y>=0; y--){
		now += data[y][now];
		result.push(now);
	}
	return result.reverse();
};

var lines;
var loadInput = function(){
	//データ作成
	input = {steps:4};
	data = [];
	for(var j=0; j<4+input.steps; j++){
		var e = lines[j];

		def = ["lines", "start", "end", "steps"];
		if(j<def.length){
			input[def[j]] = parseInt(e);
			continue;
		}
	
		//i>4
		var line = [];
		for(var i=0; i<input.lines-1; i++){
			var c = parseInt(e.charAt(i));
			if(i>0 && c==0 && line[i-1]==1) c = -1;
			line.push(c);
		}
		line.push((line[line.length-1]==1) ? -1 : 0);
		data.push(line);
	}
	input.start -= 1;
	input.end -= 1;
	lines.splice(0, 4+input.steps);
	return true;
};

var calc = function(){
	var route = f(input.start);
	if(route[route.length-1] == input.end) {
		console.log("0");
		return;
	}
	var gRoute = rf(input.end);
	
	var result = "1";
	for(var y=0; y<input.steps; y++){
		if(Math.abs(route[y]-gRoute[y]) == 1 && data[y][route[y]]==0 && data[y][gRoute[y]]==0){ //隣り合っている
			result = (y+1) + " " + (Math.min(route[y], gRoute[y])+1);
			break;
		}
	}
	
	console.log(result);
};

var exec = function(){
	if(lines[0] == "0") return; 
	loadInput();
	calc();
	exec();
};

var lines = [];
process.stdin.resume();
process.stdin.setEncoding('utf8');
process.stdin.on('data', function (chunk)
{
    chunk.trim().split('\n').forEach(function(line) {
        lines.push(line);
    });
});
 
process.stdin.on('end', function(){
	exec();
});