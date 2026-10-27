/* Original candidate for LeetCode 2046. Contract: https://leetcode.com/problems/sort-linked-list-already-sorted-using-absolute-values/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
solve accepts native linked nodes (val,next), reorders links in place and preserves node identity; JSON array input is an explicit values-only serialization adapter returning a new array.
Complexity: O(n) time and space */
"use strict";
function solve(head){if(head===null)return null;if(!Array.isArray(head)){let previous=head,current=head.next;while(current!==null&&current!==undefined){let next=current.next;if(current.val<0){previous.next=next;current.next=head;head=current;}else previous=current;current=next;}return head;}let a=[],b=[];for(const x of head)(x<0?a:b).push(x);a.reverse();return a.concat(b);}
module.exports = solve;
