"use strict";
function I(s,f){this._s=s.split("\n");this._c=0;this._l=0;this._f=f||Number}I.prototype.a=function(){var l=this._s[this._l];if(!l)return;var t=l.trim().split(" ");var a=t[this._c];this._c++;if(t.length===this._c){this._c=0;this._l++}return this._f(a)};I.prototype.l=function(){var l=this._s[this._l];if(!l)return;this._c=0;this._l++;return l.split(" ").map(this._f)};
function buildArray(r,t){let l=t||0;for(let t=r.length;t>0;t--){const n=r[t-1];l=Array(n).fill().map(()=>JSON.parse(JSON.stringify(l)))}return l}

const mod = 1e9 + 7;
function abmod(){for(var a=arguments,r=a[0],i=1;i<a.length;)r=((r>>16)*a[i]%mod*65536+(r&65535)*a[i++])%mod;return r;}

function main(input) {
  const o = new I(input);

  const n = o.a();
  const x = o.a();
  
  const s = o.l();

  s.sort((a,b) => b - a);

  var dp = Array(x+1).fill(0);
  dp[x] = 1;
  for (var i = 0; i < n; i++){
    var dp2 = Array(x+1).fill(0);
    for(var j = 0; j <= x; j++){
      dp2[j] += dp[j] * (n-i-1);
      dp2[j] %= mod;
      var m = j % s[i];
      dp2[m] += dp[j];
      dp2[m] %= mod;
    }
    dp = dp2;
  }
  var ans = 0;
  for(i = 0; i < s[n-1]; i++){
    ans += abmod(i,dp[i]);
  }

  console.log(ans % mod);
}


main(require("fs").readFileSync("/dev/stdin", "utf8"));
