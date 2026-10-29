// 391 — Perfect Rectangle. Original implementation; authored candidate, not independently qualified.
function solve(rectangles) {
  const corners = new Set(); let area=0,left=Infinity,bottom=Infinity,right=-Infinity,top=-Infinity;
  for(const [x1,y1,x2,y2] of rectangles){left=Math.min(left,x1);bottom=Math.min(bottom,y1);right=Math.max(right,x2);top=Math.max(top,y2);area+=(x2-x1)*(y2-y1);
    for(const [x,y] of [[x1,y1],[x1,y2],[x2,y1],[x2,y2]]){const key=x+','+y;if(corners.has(key))corners.delete(key);else corners.add(key);}
  }
  return area===(right-left)*(top-bottom)&&corners.size===4&&[[left,bottom],[left,top],[right,bottom],[right,top]].every(([x,y])=>corners.has(x+','+y));
}

module.exports = { solve, isRectangleCover: solve };
