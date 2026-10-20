const solve=(a,b)=>{let c=a.length-1,d=b.length-1,r=0,e='';while(c>=0||d>=0||r){const f=r+(c>=0?Number(a[c--]):0)+(d>=0?Number(b[d--]):0);e=String(f%2)+e;r=Math.floor(f/2);}return e;};
