var read = require('readline').createInterface({
  input: process.stdin,
  output: process.stdout
});
var obj;
var inLine = [];
read.on('line', function(input){inLine.push(input);});
read.on('close', function(){
  obj = init(inLine);
  myerr("-----start-----");
  var start = new Date();
  Main();
  var end = new Date() - start;
  myerr("----- end -----");
  myerr("time : " + (end) + "ms");
});
function nextInt(){return myconv(next(),1);} function nextStrArray(){return myconv(next(),2);}
function nextIntArray(){return myconv(next(),4);} function nextCharArray(){return myconv(next(),6);}
function next(){return obj.next();} function hasNext(){return obj.hasNext();}
function init(input){  
  var returnObj = {
    list : input, index : 0, max : input.length,
    hasNext : function(){return (this.index < this.max);},
    next : function(){if(!this.hasNext()){throw "ArrayIndexOutOfBoundsException これ以上ないよ";}else{var returnInput = this.list[this.index];this.index++;return returnInput;}}
  };
  return returnObj;
}
function myout(s){console.log(s);}
function myerr(s){console.error("debug:" + require("util").inspect(s,false,null));}
//[no]要素の扱い。数値型
//不明値、異常時:引数そのまま返す 1:数値へ変換
//2:半角SPで分割 4:半角SPで分割し、数値配列へ
//6:1文字で分割  7:1文字で分割し、数値配列へ
//8:半角SPで結合 9:改行で結合 0:文字なしで結合
function myconv(i,no){try{switch(no){case 1:return parseInt(i);case 2:return i.split(" ");case 4:return i.split(" ").map(Number);case 6:return i.split("");case 7:return i.split("").map(Number);case 8:return i.join(" ");case 9:return i.join("\n");case 0:return i.join("");default:return i;}}catch(e){return i;}}
function Main(){
  var one = nextIntArray();
  var N = one[0];
  var M = one[1];
  var list = new Array(N);
  for(var i = 0; i < N; i++){
    list[i] = {
      child : new Set(),
      parent : new Set(),
      from : null,
    };
  }
  for(var i = 0; i < N - 1 + M; i++){
    var tmp = nextIntArray();
    list[tmp[0] - 1].child.add(tmp[1] - 1);
    list[tmp[1] - 1].parent.add(tmp[0] - 1);
  }
  for(var i = 0; i < N; i++){
    if(list[i].parent.size == 0){
      bfs(i);
      break;
    }
  }
  var output = new Array(N);
  for(var i = 0; i < N; i++){
    output[i] = list[i].from;
    if(output[i] == null){
      output[i] = 0;
    }
  }
  myout(myconv(output,9));
  
  function bfs(index){
    var ok = [];
    var queue = [index];    
    while(queue.length > 0){
      var parent = queue.shift();
      ok.push(parent);
      var child = Array.from(list[parent].child);
      for(var i = 0; i < child.length; i++){
        list[parent].child.delete(child[i]);
        list[child[i]].parent.delete(parent);
        if(list[child[i]].parent.size == 0){
          list[child[i]].from = parent + 1;
          queue.push(child[i]);
        }
      }
    }
    //myerr(ok);
    //myerr(list);
  }
}
