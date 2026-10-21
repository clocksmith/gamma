const solve=a=>{let r=0;let n=0;for(const x of a){if(!n)r=x;n+=x===r?1:-1;}return r;};
