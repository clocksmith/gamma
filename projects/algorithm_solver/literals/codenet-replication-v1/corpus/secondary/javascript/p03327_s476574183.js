var input = "";
process.stdin.on('data', function(chunk){
  // 入力されてきた文字列をひたすら連結
input += chunk;

if ( input < 1000 )
{
console.log("ABC");
}
else
{
console.log("ABD");
}

});
