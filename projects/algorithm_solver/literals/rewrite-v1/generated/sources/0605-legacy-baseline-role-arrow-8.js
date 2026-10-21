const solve=(a,b)=>{let r=0;for(let i=0;b>0&&i<a.length;i++){if(a[i]===0&&r===0&&(a[i+1]??0)===0){b--;r=1;}else r=a[i];}return b<=0;};
