"use strict";

function solve(moveTime) {
  const n = moveTime.length, m = moveTime[0].length;
  const dist = new Float64Array(n * m).fill(1e18);
  dist[0] = 0;
  const heapT = [];
  const heapU = [];
  function push(t, u) {
    let i = heapT.length;
    heapT.push(t);
    heapU.push(u);
    while (i > 0) {
      const p = (i - 1) >> 1;
      if (heapT[p] <= heapT[i]) break;
      const tt = heapT[p]; heapT[p] = heapT[i]; heapT[i] = tt;
      const uu = heapU[p]; heapU[p] = heapU[i]; heapU[i] = uu;
      i = p;
    }
  }
  function pop() {
    const t = heapT[0], u = heapU[0];
    const lt = heapT.pop(), lu = heapU.pop();
    if (heapT.length > 0) {
      heapT[0] = lt;
      heapU[0] = lu;
      let i = 0;
      const sz = heapT.length;
      while (true) {
        let l = (i << 1) + 1, r = l + 1, b = i;
        if (l < sz && heapT[l] < heapT[b]) b = l;
        if (r < sz && heapT[r] < heapT[b]) b = r;
        if (b === i) break;
        const tt = heapT[i]; heapT[i] = heapT[b]; heapT[b] = tt;
        const uu = heapU[i]; heapU[i] = heapU[b]; heapU[b] = uu;
        i = b;
      }
    }
    return [t, u];
  }
  push(0, 0);
  const dr = [-1, 1, 0, 0], dc = [0, 0, -1, 1];
  while (heapT.length > 0) {
    const [t, u] = pop();
    if (t > dist[u]) continue;
    if (u === n * m - 1) return t;
    const r = Math.floor(u / m), c = u % m;
    const step = 1 + ((r + c) & 1);
    for (let k = 0; k < 4; k++) {
      const nr = r + dr[k], nc = c + dc[k];
      if (nr >= 0 && nr < n && nc >= 0 && nc < m) {
        const v = nr * m + nc;
        const wait = moveTime[nr][nc];
        const nt = (t > wait ? t : wait) + step;
        if (nt < dist[v]) {
          dist[v] = nt;
          push(nt, v);
        }
      }
    }
  }
  return dist[n * m - 1];
}

function minTimeToReach(moveTime) {
  return solve(moveTime);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.minTimeToReach = minTimeToReach;
