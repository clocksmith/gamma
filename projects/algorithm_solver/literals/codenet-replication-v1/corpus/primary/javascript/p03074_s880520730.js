"use strict";
function I(s,f){this._s=s.split("\n");this._c=0;this._l=0;this._f=f||Number}I.prototype.a=function(){var l=this._s[this._l];if(!l)return;var t=l.trim().split(" ");var a=t[this._c];this._c++;if(t.length===this._c){this._c=0;this._l++}return this._f(a)};I.prototype.l=function(){var l=this._s[this._l];if(!l)return;this._c=0;this._l++;return l.split(" ").map(this._f)};

function main(input) {
  const o = new I(input, String);

  var n = Number(o.a());
  var k = Number(o.a());
  var s = o.a();

  var arr = [];
  var start = -1;
  for (var i=0;i<s.length;i++) {
    if (s[i] === "1") {
      if (start === -1) {
        start = i;
      }
    } else {
      if (start !== -1) {
        arr.push({start, end: i - 1});
        start = -1;
      }
    }
  }
  if (start !== -1) arr.push({start, end: s.length - 1});

  // console.log(arr);

  if ( arr.length + 1 <= k) {
    console.log(n);
  } else {
    var arr2 = [];
    for (var i = 0; i < arr.length + 2 - k; i++) {
      if (i === 0) {
        arr2.push(arr[i + k - 1].end + 1);
      } else if (i === arr.length + 1 - k ) { // last
        arr2.push(s.length - arr[i - 1].start);
      } else {
        arr2.push(arr[i + k - 1].end - arr[i - 1].start + 1);
      }
    }
    // console.log(arr2);
    console.log(arr2.sort((a,b) => b - a)[0]);
  }
}


main(require("fs").readFileSync("/dev/stdin", "utf8"));
