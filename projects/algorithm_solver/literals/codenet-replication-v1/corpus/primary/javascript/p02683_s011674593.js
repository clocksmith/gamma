function Main(input) {
  input=input.split("\n");
  const N=input[0].split(' ')[0]-0;
  const M=input[0].split(' ')[1]-0;
  const X=input[0].split(' ')[2]-0;
  var c=[];
  var a=[];
  var temp;
  for(var i=1;i<input.length;i++){
    temp=input[i].split(' ').map(e=>{return e-0;});
    c.push(temp[0]);
    temp.shift();
    a.push(temp.concat([]));
  }
  var isBought=new Array(N);
  isBought.fill(false);
  var min=Infinity;
  loop1:
  do{
    for(var i=0;i<N;i++){
      if(isBought[i]){
        isBought[i]=false;
      }else{
        isBought[i]=true;
        break;
      }
    }
    for(var i=0;i<M;i++){
      temp=0;
      for(var j=0;j<N;j++){
        if(isBought[j]){
          temp+=a[j][i];
        }
      }
      if(temp<X){
        continue loop1;
      }
    }
    temp=0;
    for(var i=0;i<N;i++){
      if(isBought[i]){
        temp+=c[i];
      }
    }
    if(min>temp){
      min=temp;
    }
  }while(!isBought.every(e=>{return !e;}))
  console.log(min===Infinity?-1:min);
}


//*この行以降は編集しないでください（標準入出力から一度に読み込み、Mainを呼び出します）
Main(require("fs").readFileSync("/dev/stdin", "utf8"));
  
  
