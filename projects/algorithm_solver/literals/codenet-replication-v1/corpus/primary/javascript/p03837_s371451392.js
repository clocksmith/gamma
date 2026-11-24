process.stdin.resume();
process.stdin.setEncoding('ascii');

var input_stdin = "";
var input_stdin_array = "";
var input_currentline = 0;

process.stdin.on('data', function (data) {
    input_stdin += data;
});

process.stdin.on('end', function () {
    input_stdin_array = input_stdin.split("\n");
    main();    
});

function readLine() {
    return input_stdin_array[input_currentline++];
}

function main() {
	var numbers = readLine().split(" ");
	var N = parseInt(numbers[0]), M = parseInt(numbers[1]);
	
	var A=[], B=[], C=[];
    for (var i=0; i < M; i++){
        var s = readLine().split(" ");
        var a = parseInt(s[0])-1;
        var b = parseInt(s[1])-1;
        var c = parseInt(s[2]);
        A.push(a);
        B.push(b);
        C.push(c);
    }
    
    var dp = [];
    /*Declarando arreglo*/
	for (var i=0; i < N; i++){
		dp[i] = [];
		for (var j=0; j < N; j++){
			if (i!=j)
                dp[i].push(1000000000);
            else
                dp[i].push(0);
		}
	}
    
    for (var i=0; i < M; i++){
        if (dp[A[i]][B[i]] > C[i])
            dp[A[i]][B[i]] = C[i];
        if (dp[B[i]][A[i]] > C[i])
            dp[B[i]][A[i]] = C[i];
    }
    
    for (var k=0; k < N; k++){
        for (var i=0; i < N; i++){
            for (var j=0; j < N; j++){
                if (dp[i][j] > dp[i][k] + dp[k][j]){
                    dp[i][j] = dp[i][k] + dp[k][j];
                }
            }
        }
    }
    
    var ans=M;
    for (var i=0; i < M; i++){
        var shortest = false;
        for (var j=0; j < N; j++){
            if (dp[j][A[i]] + C[i] == dp[j][B[i]]){
                shortest = true;
            }
        }
        if (shortest == true) ans--;
    }
    console.log(ans);
	
	process.exit();
}