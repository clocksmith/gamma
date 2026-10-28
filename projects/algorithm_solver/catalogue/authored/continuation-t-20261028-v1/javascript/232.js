var MyQueue=function(){this.incoming=[];this.outgoing=[];};
MyQueue.prototype.push=function(x){this.incoming.push(x);};
MyQueue.prototype.pop=function(){if(!this.outgoing.length)while(this.incoming.length)this.outgoing.push(this.incoming.pop());return this.outgoing.pop();};
MyQueue.prototype.peek=function(){if(!this.outgoing.length)while(this.incoming.length)this.outgoing.push(this.incoming.pop());return this.outgoing[this.outgoing.length-1];};
MyQueue.prototype.empty=function(){return this.incoming.length===0&&this.outgoing.length===0;};
module.exports={MyQueue};
