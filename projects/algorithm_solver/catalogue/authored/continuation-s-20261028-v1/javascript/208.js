var Trie=function(){this.root=new Map();};
Trie.prototype.insert=function(word){let node=this.root;for(const c of word){if(!node.has(c))node.set(c,new Map());node=node.get(c);}node.set('',true);};
Trie.prototype.search=function(word){let node=this.root;for(const c of word){if(!node.has(c))return false;node=node.get(c);}return node.has('');};
Trie.prototype.startsWith=function(prefix){let node=this.root;for(const c of prefix){if(!node.has(c))return false;node=node.get(c);}return true;};
module.exports={Trie};
