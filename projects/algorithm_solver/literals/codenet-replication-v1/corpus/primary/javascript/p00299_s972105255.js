function main(){
	var n = scan();
	var m = scan();
	
	var e = [];
	var f = [];
	rep(m, function(){
		var s = scan('string');

		var p = s.split(/<=|>=|\*|\+|-/);
		p[0] = +p[0] - 1;
		p[1] = +p[1] - 1;
		p[2] = +p[2];

		var u;
		if(s.indexOf('*') !== -1){
			u = 2;
		}
		else{
			u = +(s.indexOf('<=') === -1);
		}

		var v = +(s.indexOf('+') === -1);

		if(u == 0){
			if(v == 0){
				e[e.length] = [p[1], p[0], -p[2]];
			}
			else{
				e[e.length] = [p[1], p[0], 0];
				e[e.length] = [p[0], p[1], p[2]];
			}
		}
		else if(u == 1){
			if(v == 0){
				e[e.length] = [p[0], p[1], -p[2]];
			}
			else{
				e[e.length] = [p[1], p[0], p[2]];
				e[e.length] = [p[0], p[1], 0];
			}
		}
		else{
			if(v == 0){
				f[f.length] = [[p[0], p[1], -p[2]], [p[1], p[0], -p[2]]];
			}
			else{
				e[e.length] = [p[1], p[0], p[2]];
				e[e.length] = [p[0], p[1], p[2]];
			}
		}
	});
	rep(n, function(i){
		e[e.length] = [i, 0, 0];
	});

	var ans = -Infinity;
	rep(1 << f.length, function(comb){
		var g = [].concat(e);
		rep(f.length, function(i){
			g[g.length] = f[i][(comb >> i) & 1];
		});

		var d = [];
		rep(n, function(i){
			d[i] = Infinity;
		});
		d[0] = 0;

		rep(n, function(){
			rep(g.length, function(j){
				var edge = g[j];
				d[edge[1]] = Math.min(d[edge[0]] + edge[2], d[edge[1]]);
			});
		});

		if(d[0] == 0){
			ans = Math.max(ans, Math.max.apply(null, d));
		}
	});

	if(ans === Infinity){
		print('inf');
	}
	else if(ans === -Infinity){
		print(-1);
	}
	else{
		print(ans);
	}
}
 
function rep(a, b, c){
	if(c == null){
		c = b;
		b = a;
		a = 0;
	}
	for(var i = a; i < b; ++i){
		c(i);
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