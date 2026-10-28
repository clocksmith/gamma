var solution=function(isBadVersion){return function(n){let low=1,high=n;while(low<high){const middle=low+Math.floor((high-low)/2);if(isBadVersion(middle))high=middle;else low=middle+1;}return low;};};
module.exports={solution};
