function solve(arrivals,w,m){const counts=new Map(),kept=Array(arrivals.length).fill(false);let discarded=0;for(let i=0;i<arrivals.length;i++){if(i>=w&&kept[i-w])counts.set(arrivals[i-w],counts.get(arrivals[i-w])-1);const value=arrivals[i],count=counts.get(value)||0;if(count===m)discarded++;else{kept[i]=true;counts.set(value,count+1);}}return discarded;}

var minArrivalsToDiscard = solve;
module.exports = solve;
