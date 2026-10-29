"use strict";
class MinHeap {
 constructor(compare=(a,b)=>a-b){this.data=[];this.compare=compare;}
 get size(){return this.data.length;}
 peek(){return this.data[0];}
 push(value){const a=this.data;let i=a.length;a.push(value);while(i){const p=(i-1)>>1;if(this.compare(a[p],value)<=0)break;a[i]=a[p];i=p;}a[i]=value;}
 pop(){const a=this.data,result=a[0],last=a.pop();if(a.length){let i=0;while(2*i+1<a.length){let c=2*i+1;if(c+1<a.length&&this.compare(a[c+1],a[c])<0)c++;if(this.compare(last,a[c])<=0)break;a[i]=a[c];i=c;}a[i]=last;}return result;}
}
function solve(courses){const chosen=new MinHeap();let elapsed=0;for(const [duration,deadline]of [...courses].sort((a,b)=>a[1]-b[1])){elapsed+=duration;chosen.push(-duration);if(elapsed>deadline)elapsed+=chosen.pop();}return chosen.size;}

function scheduleCourse(courses){return solve(courses);}
module.exports=solve;
module.exports.scheduleCourse=scheduleCourse;
