// Fresh development-only code questions; answer keys never enter the transform.
export const tasks = [
 ['reverse-nest','let x=2; for(let i=0;i<3;i++) x=2*x+3; return x;', ['35','36','37','38'],2],
 ['xor-range','let x=0; for(let i=3;i<=9;i++) x^=i; return x;', ['2','3','4','5'],0],
 ['weighted-sum','return [3,1,4].reduce((a,x,i)=>a+x*(i+1),0);', ['14','15','16','17'],3],
 ['integer-loop','let x=81,n=0; while(x>1){x=Math.floor(x/3);n++;} return n;', ['3','4','5','6'],1],
 ['mod-power','let x=1; for(let i=0;i<5;i++) x=(x*3)%11; return x;', ['1','2','3','4'],0],
 ['carry-state','let a=2,b=5; for(let i=0;i<3;i++){let t=a+2*b;a=b;b=t;} return b;', ['65','68','70','72'],2],
 ['array-slice','return [2,4,6,8,10].slice(1,-1).reduce((a,b)=>a+b,0);', ['16','18','20','22'],1],
 ['branch-count','let s=0; for(let i=1;i<=8;i++) if(i%3) s+=i; return s;', ['24','25','26','27'],3],
];
