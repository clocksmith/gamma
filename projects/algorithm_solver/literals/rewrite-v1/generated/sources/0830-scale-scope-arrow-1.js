const solve=a=>{let b=0;let c=0;let d='';const e=[];for(const f of a){if(b>0&&f!==d){if(b-c>=3){e.push([c,b-1]);}c=b;}d=f;b+=1;}if(b-c>=3){e.push([c,b-1]);}return e;};
