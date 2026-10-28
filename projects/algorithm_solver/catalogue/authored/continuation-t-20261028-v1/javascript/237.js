function ListNode(val){this.val=val;this.next=null;}
var deleteNode=function(node){const successor=node.next;node.val=successor.val;node.next=successor.next;};
module.exports={deleteNode,ListNode};
