const solve=(a,b)=>{let c=a.length-1,d=b.length-1,e=0,f='';while(c>=0||d>=0||e){const g=e+(c>=0?Number(a[c--]):0)+(d>=0?Number(b[d--]):0);f=String(g%2)+f;e=Math.floor(g/2);}return f;};
