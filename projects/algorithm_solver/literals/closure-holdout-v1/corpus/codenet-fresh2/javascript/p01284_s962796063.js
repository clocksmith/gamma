var n;
var t = [];
var m;
var s = [];
var dp = [];

function main(){
	while(n = scan()){
		rep(n, function(i){
			t[i] = scan();
		});

		m = scan();
		rep(100, function(i){
			s[i] = Infinity;
		});
		rep(m, function(i){
			var d = scan() - 1;
			s[d] = Math.min(scan(), s[d]);
		});

		rep(100, function(i){
			dp[i] = [];
		});
		dp[0][0] = 0;
		rep(1, n, function(i){
			dp[0][i] = Infinity;
		});
		rep(1, 100, function(i){
			rep(n, function(j){
				if(s[i] < t[j]){
					dp[i][j] = Infinity;
				}
				else{
					dp[i][j] = dp[i - 1][(j + n - 1) % n];
				}
			});
			dp[i][0] = Math.min(Math.min.apply(null, dp[i - 1]) + 1, dp[i][0]);
		});

		print(Math.min.apply(null, dp[99]));
	}
}

function rep(a, b, c){
	if(c === undefined){
		c = b;
		b = a;
		a = 0;
	}
	for(var i = a; i < b; ++i){
		if(c(i) === false){
			break;
		}
	}
}

var input = '';

function scan(){
	return +input.pop();
}
function scan_string(){
	return input.pop();
} 
function print(val){
	console.log(val);
}
 
process.stdin.resume();
process.stdin.setEncoding('utf8');
process.stdin.on('data', function(chunk){
	input += chunk;
});
process.stdin.on('end', function(){
	input = input.trim().split(/\s+/).reverse();
	main();
});