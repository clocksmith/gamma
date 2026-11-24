var n;
var x = [];
var y = [];
var p = [];
var q = [];

function main(){
	while(true){
		n = scan();
		if(n == 0){
			break;
		}
		rep(n, function(i){
			var s = scan('string').split(',');
			x[i] = +s[0];
			y[i] = +s[1];
		});
		rep(n, function(i){
			for(var j = i + 1; j < n; ++j){
				if(i !== j){
					var dx = x[j] - x[i];
					var dy = y[j] - y[i];
					var d = Math.sqrt(dx * dx + dy * dy);
					if(d < 2){
						dx /= d;
						dy /= d;
						var t = Math.acos(d / 2);
						var a = dx * Math.cos(t) - dy * Math.sin(t);
						var b = dx * Math.sin(t) + dy * Math.cos(t);
						p.push(a + x[i]);
						q.push(b + y[i]);
						a = dx * Math.cos(-t) - dy * Math.sin(-t);
						b = dx * Math.sin(-t) + dy * Math.cos(-t);
						p.push(a + x[i]);
						q.push(b + y[i]);
					}
				}
			}
		});
		var ans = 0;
		rep(p.length, function(i){
			var t = 0;
			rep(n, function(j){
				var dx = p[i] - x[j];
				var dy = q[i] - y[j];
				if(dx * dx + dy * dy < 1 + 1e-9){
					++t;
				}
			});
			ans = Math.max(t, ans);
		});
		print(ans);
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
 
process.stdin.resume();
process.stdin.setEncoding('utf8');
 
var input = '';
var input_index = 0;
 
function scan(type){
	if(type === 'string'){
		return input[input_index++];
	}
	else{
		return +input[input_index++];
	}
}
 
function print(val){
	console.log(val);
}
 
process.stdin.on('data', function(chunk){
	input += chunk;
});
process.stdin.on('end', function(){
	input = input.split(/\s+/);
	main();
});