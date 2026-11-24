function times(num1,num2){
  var num1str=(num1+"").split("").reverse();
  var num2str=(num2+"").split("").reverse();
  var L1=num1str.length;
  var L2=num2str.length;
  var newNumStr=[]
  for(var i=0;i<L1;i++){
    for(var j=0;j<L2;j++){
      if(newNumStr[i+j]===undefined)newNumStr[i+j]=0;
      newNumStr[i+j] += parseInt(num1str[i])*parseInt(num2str[j]);
    }
  }
  for(var k=0;k<10+10*(L1+L2);k++){
    if(newNumStr[k]===undefined)newNumStr[k]=0;
  }
  for(var k=0;k<2*(L1+L2);k++){
    if(newNumStr[k]===undefined)newNumStr[k]=0;
  }
  var l=0;
  while(newNumStr[l]||newNumStr[l]===0){
    newNumStr[l+1] += (newNumStr[l]-(newNumStr[l]%10))/10;
    newNumStr[l] = (newNumStr[l]%10).toString(10);
    l++;
  }
  newNumStr=newNumStr.reverse();
  while(isNaN(newNumStr[0])||newNumStr[0]==="0"){
    newNumStr.splice(0,1);
  }
  newNumStr=newNumStr.join("");
  return(newNumStr);
}

function adds(num1,num2){
  var num1str=(num1+"").split("").reverse();
  var num2str=(num2+"").split("").reverse();
  var L1=num1str.length;
  var L2=num2str.length;
  var newNumStr=[];
  for(var i=0;i<Math.max(L1,L2);i++){
    if(num1str[i]===undefined)num1str[i]=0;
    if(num2str[i]===undefined)num2str[i]=0;
  }
  for(var i=0;i<Math.max(L1,L2);i++){
    newNumStr[i]=parseInt(num1str[i])+parseInt(num2str[i]);
  }
  var l=0;
  while(newNumStr[l]||newNumStr[l]===0){
    newNumStr[l+1] += (newNumStr[l]-(newNumStr[l]%10))/10;
    newNumStr[l] = (newNumStr[l]%10+"");
    l++;
  }
  newNumStr=newNumStr.reverse();
  while(isNaN(newNumStr[0])||newNumStr[0]==="0"){
    newNumStr.splice(0,1);
  }
  newNumStr=newNumStr.join("");
  return(newNumStr);
}

function subtracts(num1,num2){
  var num1str=(num1+"").split("").reverse();
  var num2str=(num2+"").split("").reverse();
  var L1=num1str.length;
  var L2=num2str.length;
  var newNumStr=[];
  for(var i=0;i<Math.max(L1,L2);i++){
    if(num1str[i]===undefined)num1str[i]=0;
    if(num2str[i]===undefined)num2str[i]=0;
  }
  for(var i=0;i<Math.max(L1,L2);i++){
    newNumStr[i]=parseInt(num1str[i])-parseInt(num2str[i]);
  }
  var l=0;
  while(newNumStr[l]||newNumStr[l]===0){
    if(newNumStr[l]<0){
      newNumStr[l+1]--;
      newNumStr[l]+=10;
    }
    l++;
  }
  newNumStr=newNumStr.reverse();
  while(isNaN(newNumStr[0])||newNumStr[0]==="0"){
    newNumStr.splice(0,1);
  }
  newNumStr=newNumStr.join("");
  return(newNumStr);
}

function Main(input) {
    input = input.replace("\n","");
	input = input.split(' ');
        var K=parseInt(input[0]);
        var A=parseInt(input[1]);
        var B=parseInt(input[2]);
        var D=B-A;
        var E=K-A;
        var biscuit=0;
/*        var biscuit=((E<2)||(D<3))?(K+1):(E%2===0)?(A+E*D/2+1):(A+(E+1)*D/2);
console.log(biscuit);
*/
  if((E<1)||(D<3)){
    biscuit=K+1;
  }else if(E%2===0){
    biscuit=adds(adds(times(E/2,D),A),1);
  }else{
    biscuit=adds(times((E+1)/2,D),A);
  }
  console.log(biscuit);
}

Main(require("fs").readFileSync("/dev/stdin", "utf8"));
