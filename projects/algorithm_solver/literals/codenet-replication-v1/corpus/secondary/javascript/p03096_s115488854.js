"use strict";
function I(s,f){this._s=s.split("\n");this._c=0;this._l=0;this._f=f||Number}I.prototype.a=function(){var l=this._s[this._l];if(!l)return;var t=l.trim().split(" ");var a=t[this._c];this._c++;if(t.length===this._c){this._c=0;this._l++}return this._f(a)};I.prototype.l=function(){var l=this._s[this._l];if(!l)return;this._c=0;this._l++;return l.split(" ").map(this._f)};module.exports=I;

function main(input) {
  const o = new I(input);

  const N = o.a();
  const C = [];
  for (let i = 0; i < N; i++) {
    let cn = o.a();
    C.push(cn);
  }

  const prevPos = {};
  let results = [1];
  prevPos[C[0]] = 0;

  for (let i = 1; i < N; i++) {
    if (C[i] === C[i-1]) {
      results[i] = results[i-1];
    } else {
      let prev = prevPos[C[i]];

      if (prev !== undefined) {
        results[i] = (results[i-1] +  results[prev] ) % 1000000007;
      } else {
        results[i] = results[i-1];
      }
    }
    prevPos[C[i]] = i;
  }

  console.log(results[N-1]);
}


main(require("fs").readFileSync("/dev/stdin", "utf8"));
