"use strict"

const Main = (input) =>{
const Array =input.split("\n")
const X = parseInt(Array[0],10)
const A =parseInt(Array[1],10)
const B =parseInt(Array[2],10)
const result = (X-A)%B
console.log(result)
}

Main(require("fs").readFileSync("/dev/stdin", "utf8"));