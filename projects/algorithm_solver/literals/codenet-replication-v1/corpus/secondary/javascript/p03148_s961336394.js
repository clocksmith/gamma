"use strict";
function I(s,f){this._s=s.split("\n");this._c=0;this._l=0;this._f=f||Number}I.prototype.a=function(){var l=this._s[this._l];if(!l)return;var t=l.trim().split(" ");var a=t[this._c];this._c++;if(t.length===this._c){this._c=0;this._l++}return this._f(a)};I.prototype.l=function(){var l=this._s[this._l];if(!l)return;this._c=0;this._l++;return l.split(" ").map(this._f)};
function PriorityQueue(t,i){this._pq=[null].concat(t),this._cf=i||function(t,i){return t>i};for(let t=Math.floor(this._pq.length/2);t>=1;t--)this._maxHeapify(t)}PriorityQueue.prototype._parent=function(t){return Math.floor(t/2)},PriorityQueue.prototype._left=function(t){return 2*t},PriorityQueue.prototype._right=function(t){return 2*t+1},PriorityQueue.prototype._maxHeapify=function(t){(function t(i){let e=this._left(i),p=this._right(i),r=i;if(e<this._pq.length&&this._cf(this._pq[e],this._pq[i])&&(r=e),p<this._pq.length&&this._cf(this._pq[p],this._pq[r])&&(r=p),r!==i){let e=this._pq[i];this._pq[i]=this._pq[r],this._pq[r]=e,t.call(this,r)}}).call(this,t)},PriorityQueue.prototype.maximum=function(){return this._pq[1]},PriorityQueue.prototype.extractMax=function(){if(this._pq.length<=1)return;let t=this._pq[1];return this._pq[1]=this._pq[this._pq.length-1],this._pq.pop(),this._maxHeapify(1),t},PriorityQueue.prototype.increaseKey=function(t,i){let e=t;if(!this._pq[e]||this._cf(i,this._pq[e]))for(this._pq[e]=i;e>1&&!this._cf(this._pq[this._parent(e)],this._pq[e]);){let t=this._pq[e];this._pq[e]=this._pq[this._parent(e)],this._pq[this._parent(e)]=t,e=this._parent(e)}},PriorityQueue.prototype.insert=function(t){this._pq.push(null),this.increaseKey(this._pq.length-1,t)},PriorityQueue.prototype.size=function(t){return this._pq.length-1};

function main(input) {
  var o = new I(input);

  var n = o.a();
  var k = o.a();

  var td = [];
  for (var i = 0; i < n; i++) {
    var t = o.a();
    var d = o.a();
    td.push({t,d});
  }

  td.sort((a,b) => b.d - a.d);

  var results = [];

  var curD = 0;
  var curT = 0;
  var dup = [];
  var mark = {};
  for (var i = 0; i < k; i++) {
    if (mark[td[i].t]) {
      dup.push(td[i]);
    } else {
      curT += 1;
      mark[td[i].t] = true;
    }

    curD += td[i].d;
  }

  results.push(curD + curT * curT);

  var pq = new PriorityQueue(dup, (a,b) => a.d < b.d);

  var i = k;
  while(pq.size() > 0 && i < n) {
    if (mark[td[i].t] !== true) {
      curT += 1;
      mark[td[i].t] = true;
      var min = pq.extractMax();
      curD -= min.d;
      curD += td[i].d;
      results.push(curD + curT * curT);
    }
    i += 1;
  }

  console.log(results.sort((a,b) => b - a)[0]);
}


main(require("fs").readFileSync("/dev/stdin", "utf8"));
