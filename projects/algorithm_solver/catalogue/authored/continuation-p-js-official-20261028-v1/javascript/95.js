function TreeNode(val, left, right) {
    this.val = (val === undefined ? 0 : val);
    this.left = (left === undefined ? null : left);
    this.right = (right === undefined ? null : right);
}

var generateTrees = function(n) {
const memo=new Map();function shapes(lo,hi){if(lo>hi)return[null];const key=lo+','+hi;if(memo.has(key))return memo.get(key);const result=[];for(let value=lo;value<=hi;value++)for(const left of shapes(lo,value-1))for(const right of shapes(value+1,hi))result.push([value,left,right]);memo.set(key,result);return result;}function materialize(shape){return shape===null?null:new TreeNode(shape[0],materialize(shape[1]),materialize(shape[2]));}return shapes(1,n).map(materialize);
};
module.exports = {generateTrees, TreeNode};
