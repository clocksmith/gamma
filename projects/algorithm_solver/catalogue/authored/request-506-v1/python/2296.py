# Original implementation. Contract: https://leetcode.com/problems/design-a-text-editor/
class TextEditor:
    def __init__(self):self.left=[];self.right=[]
    def addText(self,text):self.left.extend(text)
    def deleteText(self,k):
        n=min(k,len(self.left))
        if n:del self.left[-n:]
        return n
    def cursorLeft(self,k):
        for _ in range(min(k,len(self.left))):self.right.append(self.left.pop())
        return ''.join(self.left[-10:])
    def cursorRight(self,k):
        for _ in range(min(k,len(self.right))):self.left.append(self.right.pop())
        return ''.join(self.left[-10:])
def solve(operations,arguments):
    obj=None;out=[]
    for op,args in zip(operations,arguments):
        if op=='TextEditor':obj=TextEditor();out.append(None)
        else:out.append(getattr(obj,op)(*args))
    return out
