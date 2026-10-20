const solve=a=>{let b=0;let c=0;let d='';let e=0;for(const f of a){if(f===d){c+=1;}else{b=c;c=1;d=f;}if(c<=b){e+=1;}}return e;};
