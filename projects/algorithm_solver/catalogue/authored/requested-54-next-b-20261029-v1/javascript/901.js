"use strict";
class StockSpanner {
 constructor(){this.stack=[];}
 next(price){let span=1;while(this.stack.length&&this.stack[this.stack.length-1][0]<=price)span+=this.stack.pop()[1];this.stack.push([price,span]);return span;}
}
module.exports={StockSpanner};
