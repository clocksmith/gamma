"use strict"

const Main =(input)=>{
const Array=input.split(" ")
const A=parseInt(Array[0],10)
const B=parseInt(Array[1],10)
const C=parseInt(Array[2],10)
const Answer= (A+B)>=C ?"Yes":"No"
console.log(Answer)
}




Main(require('fs').readFileSync('/dev/stdin', 'utf8'));