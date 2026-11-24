var GET = (function () {function f(s) {return new g(s);}function g(s) {this._s = s.trim().split("\n");}g.prototype.getValue = function (n) {return this._s[n];};g.prototype.getArray = function (n) {return this.stoa(this._s[n]);};g.prototype.slice = function (s, limit) {return this._s.slice(s, +limit + s || undefined).map(v => this.stox(v));};g.prototype.sliceArray = function (s, limit) {return this._s.slice(s, +limit + s || undefined).map(v => this.stoa(v));};g.prototype.stoa = function (s) {return s.split(" ").map(v => this.stox(v));};g.prototype.stox = function (v) {var i = +v;return (i === i) ? i : v;};return f;})();
var o = GET(require("fs").readFileSync("/dev/stdin", "utf8"));
function xArray(v){var a=arguments,l=a.length,r="Array(a["+--l+"]).fill(0).map(x=>{return "+v+";})";while(--l)r="Array(a["+l+"]).fill(0).map(x=>"+r+")";return eval(r);}


console.log(main());
function main() {
    var l1 = o.getArray(0);
    var N = l1[0];
    var M = l1[1];

    var info = o.sliceArray(1);
    var keys = [];
    var ans = 0;
    for (var n = N; n > 0; n--) {
        ans += 1 << n;
    }

    for (var i = 0; M * 2 > i; i = i + 2) {
        keys.push({
            a: info[i][0],
            c: info[i + 1].reduce(function (a, c) {
                return a | 1 << (c - 1);
            }, 0)
        })
    }


    var dp = (new Array(1<<N)).fill(Infinity);
    dp[0] = 0;
    for(var s = 0; 1<<N > s; s++) {
        for(var j = 0; M > j; j++) {
            var t = s | keys[j].c;
            var cost = dp[s] + keys[j].a;
            dp[t] = Math.min(dp[t], cost);
        }
    }

    return dp[(1<<N) - 1] === Infinity ? -1 : dp[(1<<N) - 1] 
}