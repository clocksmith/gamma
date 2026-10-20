function solve(a){let b=0;let c=0;for(const d of a){if(!c)b=d;c+=d===b?1:-1;}return b;}
