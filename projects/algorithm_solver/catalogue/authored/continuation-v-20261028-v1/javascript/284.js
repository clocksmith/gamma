var PeekingIterator=function(iterator){this.iterator=iterator;this.buffered=false;this.value=null;};
PeekingIterator.prototype.peek=function(){if(!this.buffered){this.value=this.iterator.next();this.buffered=true;}return this.value;};
PeekingIterator.prototype.next=function(){if(this.buffered){this.buffered=false;return this.value;}return this.iterator.next();};
PeekingIterator.prototype.hasNext=function(){return this.buffered||this.iterator.hasNext();};
module.exports={PeekingIterator};
