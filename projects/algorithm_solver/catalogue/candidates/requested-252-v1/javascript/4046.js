/**
 * 4046. Minimum Cost Path With At Most K Turns
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-cost-path-with-at-most-k-turns/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4046.Minimum%20Cost%20Path%20With%20At%20Most%20K%20Turns/README_EN.md
 * Complexity: O((k+1)mn) time, O(mn) space.
 * At most k turns means at most k+1 straight runs. Each directional sweep minimizes over all possible starts of the final run using only the previous layer as seeds. Zero-length runs allow fewer turns; visits charge the destination each time. All four directions are supported. Inputs preserved.
 */

function solve(grid,k) {
  const rows=grid.length,cols=grid[0].length,cells=rows*cols,costs=grid.flat();
  let best=new Float64Array(cells);best.fill(Infinity);best[0]=costs[0];
  for(let layer=0;layer<=k;layer++) {
    const next=best.slice();
    for(let direction=0;direction<4;direction++) {
      const work=best.slice(),forward=direction===0 || direction===2;
      const step=direction===0?-1:direction===1?1:direction===2?-cols:cols;
      for(let index=0;index<cells;index++) {
        const p=forward?index:cells-1-index;
        const valid=direction<2 ? (p%cols+step>=0 && p%cols+step<cols) : (p+step>=0 && p+step<cells);
        if(valid)work[p]=Math.min(work[p],work[p+step]+costs[p]);
        next[p]=Math.min(next[p],work[p]);
      }
    }
    best=next;
  }
  return Number.isFinite(best[cells-1])?best[cells-1]:-1;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
