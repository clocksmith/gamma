const main =(standardInput) =>{
  const s = standardInput;
  var start=-1,end=0,i=0;
  while(s[i]){
    if(s[i]=='A' && start ==-1){
    start=i;
    }else if(s[i]=='Z'){
    end=i;
    }
    i++;
  }
  var out=end+1-start;
  console.log(out);
  
}
main(require('fs').readFileSync('/dev/stdin', 'UTF-8'));