"use strict";
class WordFilter{constructor(words){this.latest=new Map();words.forEach((word,position)=>{for(let p=1;p<=word.length;p++){const prefix=word.slice(0,p)+'#';for(let s=0;s<word.length;s++)this.latest.set(prefix+word.slice(s),position);}});} f(pref,suff){const found=this.latest.get(pref+'#'+suff);return found===undefined?-1:found;}}
module.exports={WordFilter};
