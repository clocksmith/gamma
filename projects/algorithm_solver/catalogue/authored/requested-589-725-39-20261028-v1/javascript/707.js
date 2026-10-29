"use strict";
class LinkedNode{constructor(val=0,next=null){this.val=val;this.next=next;}}class MyLinkedList{constructor(){this.head=new LinkedNode();this.tail=this.head;this.size=0;}get(index){if(index<0||index>=this.size)return -1;let n=this.head.next;for(let i=0;i<index;i++)n=n.next;return n.val;}addAtHead(val){this.addAtIndex(0,val);}addAtTail(val){this.tail.next=new LinkedNode(val);this.tail=this.tail.next;this.size++;}addAtIndex(index,val){if(index>this.size)return;index=Math.max(index,0);if(index===this.size){this.addAtTail(val);return;}let n=this.head;for(let i=0;i<index;i++)n=n.next;n.next=new LinkedNode(val,n.next);this.size++;}deleteAtIndex(index){if(index<0||index>=this.size)return;let n=this.head;for(let i=0;i<index;i++)n=n.next;n.next=n.next.next;if(index===this.size-1)this.tail=n;this.size--;}}

function solve(operations,args){const instance=new MyLinkedList(...args[0]),out=[null];for(let i=1;i<operations.length;i++){const result=instance[operations[i]](...args[i]);out.push(result===undefined?null:result);}return out;}
module.exports=solve;
module.exports.MyLinkedList=MyLinkedList;
