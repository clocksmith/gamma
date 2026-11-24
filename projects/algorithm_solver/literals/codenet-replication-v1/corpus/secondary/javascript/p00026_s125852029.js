function main(){
  var localInput = input;
  var f = [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    ,[0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    ,[0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    ,[0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    ,[0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    ,[0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    ,[0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    ,[0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    ,[0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    ,[0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    ,[0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    ,[0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    ,[0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    ,[0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    ];
  
  var len = localInput.length - 1;
  for(;len--;){
    var l = localInput[len];
    var ix = parseInt(l[0]) + 2;
    var iy = parseInt(l[2]) + 2;
    switch(l[4]){
    case '3': // no-break case;
      f[iy+2][ix]++;
      f[iy-2][ix]++;
      f[iy][ix-2]++;
      f[iy][ix+2]++;
    case '2':
      f[iy+1][ix-1]++;
      f[iy+1][ix+1]++;
      f[iy-1][ix-1]++;
      f[iy-1][ix+1]++;
    case '1':
      f[iy+1][ix]++;
      f[iy][ix-1]++;
      f[iy][ix]++;
      f[iy][ix+1]++;
      f[iy-1][ix]++;
      break;
    }
  }
  
  var nd=0;//not dropped
  var md=0;//most dropped
  var y = 10;
  for(;y--;){
    var x = 10;
    for(;x--;){
      nd += !(f[y+2][x+2]);
      md = mx(f[y+2][x+2], md);
    }
  }
  
  console.log(nd);
  console.log(md);
}
   
function mx(a, b){
 var t = (a-b);
 return a - (t & (t >> 31));
}

var
input = '';
  
process.stdin.resume();
process.stdin.setEncoding('utf8');
process.stdin.on('data', function(chunk) {
  input += chunk;
});
process.stdin.on('end', function() {
  input = input.split('\n');
  main();
});