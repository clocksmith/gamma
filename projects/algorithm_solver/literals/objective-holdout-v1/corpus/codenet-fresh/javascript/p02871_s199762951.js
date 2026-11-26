var input = require("fs").readFileSync("/dev/stdin", "utf8").trim().split("\n");
var obj = {
  "list" : input, "index" : 0, "max" : input.length,
  "hasNext" : function(){return (this.index < this.max);},
  "next" : function(){
    if(!this.hasNext()){return "";}
    var returnObj = this.list[this.index];
    this.index++;
    return returnObj;
  }
}
Main();
function next(){return obj.next();}
function nextInt(){return myconv(next(),1);}
function nextStrArray(){return myconv(next(),2);}//半角スペース分割
function nextIntArray(){return myconv(next(),4);}//半角スペース + 数値化
function nextCharArray(){return myconv(next(),6);}//1文字分割
function hasNext(){return obj.hasNext();}
function myout(t){console.log(t);}//標準出力
function myerr(t){console.error(t);}//標準エラー出力
//[no]要素の扱い。数値型
//不明値、異常時:引数そのまま返す　1:数値へ変換
//2:半角SPで分割 4:半角SPで分割し、数値配列へ
//6:1文字で分割  7:1文字で分割し、数値配列へ
//8:半角SPで結合 9:改行で結合 0:文字なしで結合
function myconv(i,no){try{switch(no){case 1:return parseInt(i);case 2:return i.split(" ");case 4:return i.split(" ").map((a)=>Number(a));case 6:return i.split("");case 7:return i.split("").map((a)=>Number(a));case 8:return i.join(" ");case 9:return i.join("\n");case 0:return i.join("");default:return i;}}catch(e){return i;}}
function Main(){
  var output = myconv(new Array(10000).fill("-1"),9);
  myout(output);
}
