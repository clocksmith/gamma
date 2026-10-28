var WordDictionary=function(){this.root=new Map();};
WordDictionary.prototype.addWord=function(word){let node=this.root;for(const c of word){if(!node.has(c))node.set(c,new Map());node=node.get(c);}node.set('',true);};
WordDictionary.prototype.search=function(word){let frontier=[this.root];for(const c of word){const following=[];for(const node of frontier){if(c==='.'){for(const [key,child] of node){if(key!=='')following.push(child);}}else if(node.has(c))following.push(node.get(c));}if(!following.length)return false;frontier=following;}return frontier.some(node=>node.has(''));};
module.exports={WordDictionary};
