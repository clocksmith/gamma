"use strict"

const arg_str = require('fs').readFileSync('/dev/stdin', 'UTF-8')
const args_lines = arg_str.split('\n')
const N = args_lines[0]
const anagrams = args_lines.slice(1)

const anagrams_sort = anagrams.map(x=>{
  return x.split('').sort((a,b)=>a>b).join('')
})

const result_dict = {}
anagrams_sort.map(x=>{
  if(result_dict[x] > -1){
    result_dict[x]++
  }else{
    result_dict[x] = 0
  }
})

let result = 0

Object.keys(result_dict).forEach( function(key) {
  const v = result_dict[key]
  result += v * (v+1) / 2
})

console.log(result)