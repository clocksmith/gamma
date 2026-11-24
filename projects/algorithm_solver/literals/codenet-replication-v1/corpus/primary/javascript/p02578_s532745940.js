function Main(input) {
  input=input.split("\n");
  const N=input[0]-0;
  const height=input[1].split(' ').map(e=>{
    return e-0;
  });
  var max=0;
  var ret=0;
  height.forEach(e=>{
    if(max<e){
      max=e;
    }else{
      ret+=max-e;
    }
  });
  console.log(ret);
}


//*この行以降は編集しないでください（標準入出力から一度に読み込み、Mainを呼び出します）
Main(require("fs").readFileSync("/dev/stdin", "utf8"));
  
  
