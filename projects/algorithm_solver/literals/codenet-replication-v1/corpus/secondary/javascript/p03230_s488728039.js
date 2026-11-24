//Don't have to see. start------------------------------------------
var read = require('readline').createInterface({
  input: process.stdin, output: process.stdout
});
var obj; var inLine = [];
read.on('line', function(input){inLine.push(input);});
read.on('close', function(){
  obj = init(inLine);
  console.error("\n");
  var start = Date.now();
  Main();
  var end = Date.now() - start;
  myerr("time : " + (end) + "ms");
  myerr("memory : " + Math.round(process.memoryUsage().heapTotal / 1024) + "KB");
});
function makeClone(obj){return JSON.parse(JSON.stringify(obj));}
function nextInt(){return myconv(next(),1);} function nextStrArray(){return myconv(next(),2);}
function nextIntArray(){return myconv(next(),4);} function nextCharArray(){return myconv(next(),6);}
function next(){return obj.next();} function hasNext(){return obj.hasNext();}
function init(input){  
  return {
    list : input, index : 0, max : input.length,
    hasNext : function(){return (this.index < this.max);},
    next : function(){if(this.hasNext()){return this.list[this.index++];}else{throw "ArrayIndexOutOfBoundsException ‚There is no more input";}}
  };
}
function myout(s){console.log(s);}
function myerr(s){console.error("debug:" + require("util").inspect(s,false,null));}
//param "no" is
//unknown or outlier : return i. 1: parseInt.
//2: split space. 4: split space and parseInt.
//6: split 1 character. 7: split 1 character and parseInt.
//8: join space. 9: join nextline. 0: join no character.
function myconv(i,no){try{switch(no){case 1:return parseInt(i);case 2:return i.split(" ");case 4:return i.split(" ").map(Number);case 6:return i.split("");case 7:return i.split("").map(Number);case 8:return i.join(" ");case 9:return i.join("\n");case 0:return i.join("");default:return i;}}catch(e){return i;}}

//Don't have to see. end------------------------------------------
function Main(){
  var N = nextInt();
  var check = 0;
  var isOK = false;
  while(check <= N){
    if((check * (check + 1)) / 2 == N){
      isOK = true;
      break;
    }
    check++;
  }
  if(!isOK){
    myout("No");
    return;
  }
  myout("Yes");
  var list = new Array(check + 1);
  for(var i = 0; i < check + 1; i++){
    list[i] = new Array(check);
  }
  var count = 1;
  for(var i = 0; i < check; i++){
    for(var j = i; j < check; j++){
      list[i][j] = count;
      list[j + 1][i] = count;
      count++;
    }
  }
  myerr(list);
  myout(list.length);
  var output = new Array(list.length);
  for(var i = 0; i < list.length; i++){
    list[i].unshift(check);
    output[i] = list[i].join(" ");
  }
  myout(myconv(output, 9));
}
