// Independently authored PUBLIC runtime control, not a corpus algorithm.
const gammaInitialMin = Math.min, gammaInitialMax = Math.max;
const gammaInitialIterator = Array.prototype[Symbol.iterator];
const gammaInitialValues = Array.prototype.values;
function solve() {
 const minDescriptor=Object.getOwnPropertyDescriptor(Math,'min');
 const maxDescriptor=Object.getOwnPropertyDescriptor(Math,'max');
 const order=[];
 const evaluated=Math.max((order.push(1),2),(order.push(2),3));
 const nested=[1,2], array=[nested,3], values=[];
 for(const value of array)values.push(value);
 const holes=[];for(const value of [,5])holes.push(value);
 return {
  ordinary:Math.min(2,-3,4)===-3&&Math.max(2,-3,4)===4,
  signed_zero:Object.is(Math.min(+0,-0),-0)&&Object.is(Math.max(-0,+0),+0),
  nan:Number.isNaN(Math.min(NaN,1))&&Number.isNaN(Math.max(1,NaN)),
  infinities:Math.min(Infinity,3)===3&&Math.max(-Infinity,3)===3&&Math.min(-Infinity,3)===-Infinity&&Math.max(Infinity,3)===Infinity,
  empty:Math.min()===Infinity&&Math.max()===-Infinity,
  argument_order:evaluated===3&&order.length===2&&order[0]===1&&order[1]===2,
  direct_descriptors:minDescriptor.value===Math.min&&maxDescriptor.value===Math.max&&!minDescriptor.get&&!maxDescriptor.get&&!minDescriptor.set&&!maxDescriptor.set,
  native_intrinsics:Function.prototype.toString.call(Math.min).includes('[native code]')&&Function.prototype.toString.call(Math.max).includes('[native code]'),
  extrema_unchanged:Math.min===gammaInitialMin&&Math.max===gammaInitialMax,
  iterator_identity:Array.prototype[Symbol.iterator]===Array.prototype.values&&Array.prototype[Symbol.iterator]===gammaInitialIterator&&Array.prototype.values===gammaInitialValues,
  iterator_alias:values.length===2&&values[0]===nested&&values[1]===3&&array[0]===nested&&nested[0]===1&&nested[1]===2,
  iterator_holes:holes.length===2&&holes[0]===undefined&&holes[1]===5,
  native_iterator:Function.prototype.toString.call(Array.prototype.values).includes('[native code]')
 };
}
