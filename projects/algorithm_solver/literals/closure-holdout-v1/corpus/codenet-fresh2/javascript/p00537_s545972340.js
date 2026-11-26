function main(){
	var n = scan();
	var m = scan();
	var p = Array(m);
	rep(m, function(i){
		p[i] = scan() - 1;
	});
	var a = Array(n - 1);
	var b = Array(n - 1);
	var c = Array(n - 1);
	rep(n - 1, function(i){
		a[i] = scan();
		b[i] = scan();
		c[i] = scan();
	});
	var x = Array(n);
	rep(n, function(i){
		x[i] = 0;
	});
	rep(m - 1, function(i){
		var s = Math.min(p[i], p[i + 1]);
		var t = Math.max(p[i], p[i + 1]);
		x[s] += 1;
		x[t] -= 1;
	});
	rep(n - 1, function(i){
		x[i + 1] += x[i];
	});
	var ans = [0, 0];
	rep(n - 1, function(i){
		v = Math.min(a[i] * x[i], b[i] * x[i] + c[i]);
		ans[1] += Math.floor((v + ans[0]) / 1e12);
		ans[0] = (v + ans[0]) % 1e12;
	});
	if(ans[1] == 0){
		print(ans[0]);
	}
	else{
		print('' + ans[1] + (Array(12).join('0') + ans[0]).slice(-12));
	}
}

function rep(n, func){
	for(var i = 0; i < n; ++i){
		func(i);
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