function solve(num){function prime(x){if(x<2)return false;if(x%2===0)return x===2;for(let d=3;d*d<=x;d+=2)if(x%d===0)return false;return true;}const text=String(num);for(let i=1;i<=text.length;i++)if(!prime(Number(text.slice(0,i)))||!prime(Number(text.slice(-i))))return false;return true;}

var completePrime = solve;
module.exports = solve;
