// 407 — Trapping Rain Water II. Original implementation; authored candidate, not independently qualified.
function solve(heightMap) {
  if(!heightMap.length||!heightMap[0].length)return 0;
  const rows=heightMap.length,cols=heightMap[0].length,seen=Array.from({length:rows},()=>Array(cols).fill(false)),heap=[];
  function push(item){heap.push(item);let i=heap.length-1;while(i>0){const p=Math.floor((i-1)/2);if(heap[p][0]<=item[0])break;heap[i]=heap[p];i=p;}heap[i]=item;}
  function pop(){const result=heap[0],last=heap.pop();if(heap.length){let i=0;while(i*2+1<heap.length){let c=i*2+1;if(c+1<heap.length&&heap[c+1][0]<heap[c][0])c++;if(heap[c][0]>=last[0])break;heap[i]=heap[c];i=c;}heap[i]=last;}return result;}
  for(let r=0;r<rows;r++)for(let c=0;c<cols;c++)if(r===0||c===0||r===rows-1||c===cols-1){seen[r][c]=true;push([heightMap[r][c],r,c]);}
  let total=0;
  while(heap.length){const [level,r,c]=pop();for(const [nr,nc] of [[r+1,c],[r-1,c],[r,c+1],[r,c-1]])if(nr>=0&&nr<rows&&nc>=0&&nc<cols&&!seen[nr][nc]){seen[nr][nc]=true;total+=Math.max(0,level-heightMap[nr][nc]);push([Math.max(level,heightMap[nr][nc]),nr,nc]);}}
  return total;
}

module.exports = { solve, trapRainWater: solve };
