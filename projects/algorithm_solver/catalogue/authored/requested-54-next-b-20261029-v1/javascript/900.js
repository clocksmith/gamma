"use strict";
class RLEIterator {
 constructor(encoding){this.encoding=encoding.slice();this.index=0;this.used=0;}
 next(n){while(this.index<this.encoding.length){const remaining=this.encoding[this.index]-this.used;if(n<=remaining){this.used+=n;return this.encoding[this.index+1];}n-=remaining;this.index+=2;this.used=0;}return -1;}
}
module.exports={RLEIterator};
