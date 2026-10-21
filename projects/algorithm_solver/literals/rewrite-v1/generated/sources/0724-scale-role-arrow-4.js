const solve=a=>{let r=0;for(const x of a){r+=x;}let n=0;for(let i=0;i<a.length;i+=1){r-=a[i];if(n===r){return i;}n+=a[i];}return-1;};
