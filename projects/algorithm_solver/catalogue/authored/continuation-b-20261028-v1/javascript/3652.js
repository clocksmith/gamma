function solve(prices,strategy,k){
 const original=[0],values=[0];for(let i=0;i<prices.length;i++){original.push(original[i]+prices[i]*strategy[i]);values.push(values[i]+prices[i]);}
 let gain=0;for(let start=0;start+k<=prices.length;start++)gain=Math.max(gain,-original[start+k]+original[start]+values[start+k]-values[start+k/2]);return original[prices.length]+gain;
}

var maxProfit = solve;
module.exports = solve;
