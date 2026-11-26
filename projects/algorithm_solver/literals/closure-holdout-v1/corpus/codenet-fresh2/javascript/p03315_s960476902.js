var main = function(s) {
s=s.split('');
  var count=0;
  for(var i=0;i<4;i++){
  if(s[i] === '+'){
	count++;
  } else{
    count--;
  }
  }
  var output = count;
    console.log(output);
    return 0; 
}

main(require("fs").readFileSync("/dev/stdin", "utf8"));
