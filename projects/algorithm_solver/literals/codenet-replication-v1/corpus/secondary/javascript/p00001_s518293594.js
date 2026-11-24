process.stdin.resume();
process.stdin.setEncoding('utf8');
// Here your code !
process.stdin.on("data",function(chunk){
    var line = chunk.trim().split("\n").map(function(e){return parseInt(e)});
    console.log(line.sort(function(a,b){return b-a}).slice(0,3).join("\n"))
    
})