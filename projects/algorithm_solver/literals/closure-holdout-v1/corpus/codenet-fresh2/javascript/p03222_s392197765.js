"use strict";

// 21:39
function I(s,f){this._s=s.split("\n");this._c=0;this._l=0;this._f=f||Number}I.prototype.a=function(){var l=this._s[this._l];if(!l)return;var t=l.trim().split(" ");var a=t[this._c];this._c++;if(t.length===this._c){this._c=0;this._l++}return this._f(a)};I.prototype.l=function(){var l=this._s[this._l];if(!l)return;this._c=0;this._l++;return l.split(" ").map(this._f)};
function buildArray(r,t){let l=t||0;for(let t=r.length;t>0;t--){const n=r[t-1];l=Array(n).fill().map(()=>JSON.parse(JSON.stringify(l)))}return l}

const mod = 1000000007;

function main(input) {
  var o = new I(input);

  var h = o.a();
  var w = o.a();
  var k = o.a();

  var wc = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55];
  var dp = buildArray([h, w], 0);

  dp[0][0] = wc[w - 1];
  dp[0][1] = wc[w - 2];

  for (var i = 1; i < h; i++) {
    for (var j = 0; j < w; j++) {
      dp[i][j] += dp[i-1][j] * (wc[w - j - 1] * wc[j]);
      if (j - 1 >= 0) {
        dp[i][j] += dp[i-1][j-1] * (wc[w - j - 1] * wc[j - 1]);
      }
      if ( j + 1 <= w - 1) {
        dp[i][j] += dp[i-1][j+1] * (wc[w - j - 2] * wc[j]);
      }

      dp[i][j] %= mod;
    }
  }

  console.log(dp[h-1][k-1]);
}


main(require("fs").readFileSync("/dev/stdin", "utf8"));
