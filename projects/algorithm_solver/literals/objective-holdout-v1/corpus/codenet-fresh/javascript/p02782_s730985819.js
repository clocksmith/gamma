function Main(input) {
	input = input.trim().split("\n").map(function(x) { return x.split(" ")});
	let C = 1e9 + 7;
	let C2 = 1e5;
	let line = input[0].map(e => parseInt(e, 10));
	let r = [line[0], line[2]];
	let c = [line[1], line[3]];

	v_nCr1 = nCr_amari(r[1] + 1 + c[0], c[0] + 1, c[1] - c[0], C, C2);
	v_nCr2 = nCr_amari(r[0] + c[0], c[0] + 1, c[1] - c[0], C, C2);
	if (v_nCr2 === 0) v_nCr2 = Array.from({length: v_nCr1.length}, () => 0);

	let ans = 0;
	for (let i = 0; i < v_nCr1.length; i++){
		ans += (v_nCr1[i] - v_nCr2[i])
		ans = mod(ans, C);
	}
	
	console.log(ans);

}

function mod(i, j) {
    return (i % j) < 0 ? (i % j) + 0 + (j < 0 ? -j : j) : (i % j + 0);
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
    for (var i = 2; i <= MAX + n; i++){
        fac.push(fac[i - 1] * i % MOD);
        inv.push(MOD - kakeruR(inv[MOD%i], (MOD / i | 0), MOD, C2) % MOD);
        finv.push(kakeruR(finv[i - 1],inv[i] ,MOD,C2));
    }
    //二項係数計算
    if (n < k) return 0;
    if (n < 0 || k < 0) return 0;
    for (var i = 0; i <= MAX; i++){
    v_ans.push(kakeruR(kakeruR(fac[n + i] , finv[k + i],MOD,C2), finv[n - k],MOD,C2));
    }
    return v_ans;
}


Main(require("fs").readFileSync("/dev/stdin", "utf8"));
