function FIFO(){this.first=null;this.last=null;this.length=0;}
FIFO.prototype.enqueue=function(value){const node={value,next:null};if(this.last!==null)this.last.next=node;else this.first=node;this.last=node;this.length++;};
FIFO.prototype.dequeue=function(){const value=this.first.value;this.first=this.first.next;if(this.first===null)this.last=null;this.length--;return value;};
FIFO.prototype.front=function(){return this.first.value;};
FIFO.prototype.size=function(){return this.length;};
FIFO.prototype.empty=function(){return this.length===0;};
var MyStack=function(){this.queue=new FIFO();};
MyStack.prototype.push=function(x){const size=this.queue.size();this.queue.enqueue(x);for(let i=0;i<size;i++)this.queue.enqueue(this.queue.dequeue());};
MyStack.prototype.pop=function(){return this.queue.dequeue();};
MyStack.prototype.top=function(){return this.queue.front();};
MyStack.prototype.empty=function(){return this.queue.empty();};
module.exports={MyStack};
