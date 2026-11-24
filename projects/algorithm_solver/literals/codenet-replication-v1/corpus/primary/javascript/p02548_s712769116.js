process.stdin.resume()
process.stdin.setEncoding('utf8')
var g_input = ''
process.stdin.on('data', function(chunk) {
    g_input += chunk
})
process.stdin.on('end', function() {
    main(g_input.split(/\r?\n/))
})
function main(input){
  input = Number(input[0])
  let c = 0
  for(let i=1;i<=input;i++){
    for(let j=1;j<=input;j++){
      //console.log(`${i}${j}`)
      if(j*i<input){
        c++
      }else{
        break
      }
    }
  }
  console.log(c)
}