"use strict";
class OrderedStream {
 constructor(n){this.values=Array(n).fill(null);this.next=0;}
 insert(idKey,value){this.values[idKey-1]=value;const chunk=[];while(this.next<this.values.length&&this.values[this.next]!==null){chunk.push(this.values[this.next]);this.next++;}return chunk;}
}
module.exports={OrderedStream};
