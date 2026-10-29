"use strict";
function solve(points){const groups=new Map();for(let i=0;i<points.length;i++)for(let j=0;j<i;j++){const [x,y]=points[i],[a,b]=points[j],key=[x+a,y+b,(x-a)**2+(y-b)**2].join(',');if(!groups.has(key))groups.set(key,[]);groups.get(key).push([i,j]);}let best=Infinity;for(const group of groups.values())for(let p=0;p<group.length;p++)for(let q=0;q<p;q++){const [i,j]=group[p],[k]=group[q],[ax,ay]=points[i],[bx,by]=points[j],[cx,cy]=points[k];const area=Math.abs((ax-cx)*(by-cy)-(ay-cy)*(bx-cx));if(area)best=Math.min(best,area);}return best===Infinity?0:best;}

function minAreaFreeRect(points){return solve(points);}
module.exports=solve;
module.exports.minAreaFreeRect=minAreaFreeRect;
