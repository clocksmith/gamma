function ListNode(val,next){this.val=val===undefined?0:val;this.next=next===undefined?null:next;}
var reverseList=function(head){let previous=null;while(head!==null){const following=head.next;head.next=previous;previous=head;head=following;}return previous;};
module.exports={reverseList,ListNode};
