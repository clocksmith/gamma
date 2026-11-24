function main(arg) {
	var tmp = arg.split("\n")[0];
	var t = false;
	do {
        t = /keyence$/.test(tmp);
        if (t) break;
        t = /^keyence/.test(tmp);
        if (t) break;
        t = /^k.*eyence$/.test(tmp);
        if (t) break;
        t = /^ke.*yence$/.test(tmp);
        if (t) break;
        t = /^key.*ence$/.test(tmp);
        if (t) break;
        t = /^keye.*nce$/.test(tmp);
        if (t) break;
        t = /^keyen.*ce$/.test(tmp);
        if (t) break;
        t = /^keyenc.*e$/.test(tmp);
        if (t) break;
        t = /^keyence$/.test(tmp);
        if (t) break;
	} while (0);
	if (t) {
		console.log("YES");
	} else {
		console.log("NO");
	}
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));