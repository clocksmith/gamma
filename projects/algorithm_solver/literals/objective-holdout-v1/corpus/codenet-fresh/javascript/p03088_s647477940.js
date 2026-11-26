"use strict";
function I(s,f){this._s=s.split("\n");this._c=0;this._l=0;this._f=f||Number}I.prototype.a=function(){var l=this._s[this._l];if(!l)return;var t=l.trim().split(" ");var a=t[this._c];this._c++;if(t.length===this._c){this._c=0;this._l++}return this._f(a)};I.prototype.l=function(){var l=this._s[this._l];if(!l)return;this._c=0;this._l++;return l.split(" ").map(this._f)};
function buildArray(r,e){let n=e||0;for(let e=r.length;e>0;e--){const t=r[e-1];if("number"!=typeof t)return void console.error("Arguments must be number");n=Array(t).fill().map(()=>JSON.parse(JSON.stringify(n)))}return n}

function main(input) {
  const o = new I(input, String);

  const N = o.a();

  const dp = buildArray([Number(N + 10), 4, 4, 4]);

  dp[0][3][3][3] = 1;
  for (let i = 1; i <= N; i++) {
    for (let s1 = 0; s1 < 4; s1++) {
      for (let s2 = 0; s2 < 4; s2++) {
        for (let s3 = 0; s3 < 4; s3++) {
          if (dp[i - 1][s1][s2][s3] === 0) continue;

          for (let a = 0; a < 4; a++) {
            if (s2 === 0 && s3 === 2 && a ===1) continue;
            if (s2 === 0 && s3 === 1 && a ===2) continue;
            if (s2 === 2 && s3 === 0 && a ===1) continue;
            if (s1 === 0 && s2 === 2 && a ===1) continue;
            if (s1 === 0 && s3 === 2 && a ===1) continue;
            dp[i][s2][s3][a] += dp[i - 1][s1][s2][s3];
            dp[i][s2][s3][a] %= 1000000007
          }
        }
      }
    }
  }

  let total = 0;
  for (let s1 = 0; s1 < 4; s1++) {
    for (let s2 = 0; s2 < 4; s2++) {
      for (let s3 = 0; s3 < 4; s3++) {
        total += dp[N][s1][s2][s3];
      }
    }
  }
  console.log(total % 1000000007);
}

main(require("fs").readFileSync("/dev/stdin", "utf8"));
