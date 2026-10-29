"use strict";
class RecentCounter{constructor(){this.times=[];this.head=0;}ping(t){this.times.push(t);while(this.times[this.head]<t-3000)this.head++;return this.times.length-this.head;}}
module.exports={RecentCounter};
