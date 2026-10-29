"use strict";
class ThroneInheritance {
 constructor(kingName){this.king=kingName;this.children=new Map([[kingName,[]]]);this.dead=new Set();}
 birth(parentName,childName){this.children.get(parentName).push(childName);this.children.set(childName,[]);}
 death(name){this.dead.add(name);}
 getInheritanceOrder(){const stack=[this.king],answer=[];while(stack.length){const name=stack.pop();if(!this.dead.has(name))answer.push(name);const children=this.children.get(name);for(let i=children.length-1;i>=0;i--)stack.push(children[i]);}return answer;}
}
module.exports={ThroneInheritance};
