function solve(towers,center,radius){let best=null;for(const [x,y,q] of towers){if(Math.abs(x-center[0])+Math.abs(y-center[1])>radius)continue;if(best===null||q>best[2]||(q===best[2]&&(x<best[0]||(x===best[0]&&y<best[1]))))best=[x,y,q];}return best===null?[-1,-1]:[best[0],best[1]];}

var bestTower = solve;
module.exports = solve;
