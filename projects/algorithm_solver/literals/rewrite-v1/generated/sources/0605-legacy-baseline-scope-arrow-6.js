const solve=(a,b)=>{let c=0;for(let d=0;b>0&&d<a.length;d++){if(a[d]===0&&c===0&&(a[d+1]??0)===0){b--;c=1;}else c=a[d];}return b<=0;};
