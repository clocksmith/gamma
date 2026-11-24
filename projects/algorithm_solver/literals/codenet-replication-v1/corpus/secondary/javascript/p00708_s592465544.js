var n;
var c = [];
var u = [];
var f = [];

function dist(i, j){
	var s = 0;
	rep(3, function(k){
		var d = c[i][k] - c[j][k];
		s += d * d;	
	});
	s = Math.sqrt(s);
	return Math.max(s - c[i][3] - c[j][3], 0);
}

function main(){
	while(n = scan()){
		rep(n, function(i){
			c[i] = [scan(), scan(), scan(), scan()];
		});

		rep(n, function(i){
			f[i] = Infinity;
		});

		var ans = 0;
		f[0] = 0;
		rep(n, function(){
			var v = -1;
			rep(n, function(i){
				if(!u[i] && (v === -1 || f[i] < f[v])){
					v = i;
				}
			});
			ans += f[v];
			u[v] = true;
			rep(n, function(i){
				f[i] = Math.min(dist(v, i), f[i]);
			});
		});

		ans = Math.round(ans * 1000);
		var ans1 = Math.floor(ans / 1000);
		var ans2 = ans % 1000;
		print(ans1 + '.' + ('00' + ans2).slice(-3));

		u = [];
	}
}

function rep(a, b, c, u){
	if(c === u){
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