function solve(a){let b='1';for(let i=1;i<a;i++){let a='';for(let i=0;i<b.length;){let c=i+1;while(c<b.length&&b[c]===b[i]){c++;}a+=String(c-i)+b[i];i=c;}b=a;}return b;}
