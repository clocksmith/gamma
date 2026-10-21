const solve=a=>{const b=a<0?-1:1;const c=b<0?2147483648:2147483647;let d=Math.abs(a);let e=0;while(d>0){const a=d%10;if(e>Math.floor((c-a)/10)){return 0;}e=e*10+a;d=Math.trunc(d/10);}return b*e;};
