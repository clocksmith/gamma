function solve(s){const n=s.length;let palTwo=new Uint8Array(n+1).fill(1),palOne=new Uint8Array(n).fill(1),almostTwo=new Uint8Array(n+1),almostOne=new Uint8Array(n).fill(1),answer=1;for(let length=2;length<=n;length++){const count=n-length+1,pal=new Uint8Array(count),almost=new Uint8Array(count);for(let l=0;l<count;l++){const same=s[l]===s[l+length-1];pal[l]=Number(same&&Boolean(palTwo[l+1]));almost[l]=Number(Boolean(palOne[l]||palOne[l+1]||(same&&almostTwo[l+1])));if(almost[l])answer=length;}palTwo=palOne;palOne=pal;almostTwo=almostOne;almostOne=almost;}return answer;}

var almostPalindromic = solve;
module.exports = solve;
