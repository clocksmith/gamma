"use strict";
function I(s,f){this._s=s.split("\n");this._c=0;this._l=0;this._f=f||Number}I.prototype.a=function(){var l=this._s[this._l];if(!l)return;var t=l.trim().split(" ");var a=t[this._c];this._c++;if(t.length===this._c){this._c=0;this._l++}return this._f(a)};I.prototype.l=function(){var l=this._s[this._l];if(!l)return;this._c=0;this._l++;return l.split(" ").map(this._f)};
function sieveOfEratosthenes(e){const t=new Array(e+1).fill(!0);t[0]=!1,t[1]=!1;const n=[];for(let r=2;r<=e;r+=1)if(!0===t[r]){n.push(r);let f=r*r;for(;f<=e;)t[f]=!1,f+=r}return n}

var primes = sieveOfEratosthenes(100000);
function main(input) {
  var o = new I(input);

  var n = o.a();
  var a = [];

  for (var i = 0; i <= n; i++) {
    a.push(o.a());
  }

  a = a.reverse();

  let agcd = a[0];
  for (var i = 1; i <= n; i++) {
    agcd = Math.abs(gcd(agcd, a[i]));
  }

  a = a.map(x => x/agcd);


  var ans = [];
  primes.filter(p => p <= n).forEach(prime => {
    if (a[0] % prime !== 0) return;
    for (var i = 1; i < prime; i++) {
      var j = i;
      var ajsum = 0;
      while (j <= n) {
        ajsum += a[j];
        j += prime - 1;
      }
      if (ajsum % prime !== 0) return;
    }
    ans.push(prime);
  });

  var i = 0;
  while (agcd > 1 && i < primes.length) {
    if (agcd % primes[i] === 0) {
      ans.push(primes[i]);
      while(agcd % primes[i] === 0) {
        agcd = agcd / primes[i];
      }
    }
    i += 1;
  }
  if (agcd > 1) {
    ans.push(agcd);
  }

  ans.sort((a,b) => a - b);
  var prev;
  for (var i = 0; i < ans.length; i++) {
    if (prev !== ans[i]) {
      console.log(ans[i]);
    }
    prev = ans[i];
  }
}

function gcd(a, b) {
  if (b === 0) return a;
  return gcd(b, a%b);
}


main(require("fs").readFileSync("/dev/stdin", "utf8"));
