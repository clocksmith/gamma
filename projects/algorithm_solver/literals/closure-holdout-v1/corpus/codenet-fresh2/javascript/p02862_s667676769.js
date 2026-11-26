function Main(input) {
	input = input.trim().split("\n").map(function(x) { return x.split(" ")});    
	var C = 1e+9 +7;
	var C2 = 1e+5;
	var X = parseInt(input[0][0], 10);
	var Y = parseInt(input[0][1], 10);
	var ans = 0;
	var n = (X + Y) / 3;
	var r = (4*X - 2*Y) / 6;
	var r2 = (4*Y - 2*X) / 6
	if (r >= 0 && r2 >= 0 && Number.isInteger(r)){
		var tmp = nCr_amari(n, r, 1, C, C2);
		ans = tmp[0];
	}
	console.log(ans);
}

function kakeruR(a, b, C, C2){
    var tmpQ, tmpR, ans;
    tmpQ = (b / C2 | 0);
    tmpR = b - (tmpQ * C2);
    ans = (a * tmpQ % C) * C2 % C + (a * tmpR);
    ans %= C;
    return ans;
}


function nCr_amari(n, k, MAX, MOD, C2) { //return [nCk, n+1Ck+1, ..., n+maxCk+max]
    // 前処理
    var v_ans = [ ];
    var fac, finv, inv;
    fac = [1,1];
    finv = [1,1];
    inv = [0,1];
    for (var i = 2; i < MAX + n; i++){
        fac.push(fac[i - 1] * i % MOD);
        inv.push(MOD - kakeruR(inv[MOD%i], (MOD / i | 0), MOD, C2) % MOD);
        finv.push(kakeruR(finv[i - 1],inv[i] ,MOD,C2));
    }
    //二項係数計算
    if (n < k) return 0;
    if (n < 0 || k < 0) return 0;
    for (var i = 0; i < MAX; i++){
    v_ans.push(kakeruR(kakeruR(fac[n + i] , finv[k + i],MOD,C2), finv[n - k],MOD,C2));
    }
    return v_ans;
}

Main(require("fs").readFileSync("/dev/stdin", "utf8"));
