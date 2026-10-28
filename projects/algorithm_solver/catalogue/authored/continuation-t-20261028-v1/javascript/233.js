var countDigitOne=function(n){let answer=0;for(let factor=1;factor<=n;factor*=10){const high=Math.floor(n/(factor*10)),current=Math.floor(n/factor)%10,low=n%factor;answer+=high*factor;if(current===1)answer+=low+1;else if(current>1)answer+=factor;}return answer;};
module.exports={countDigitOne};
