"use strict";
function solve(row) {
const seats=row.slice(),where=new Array(seats.length).fill(0);seats.forEach((person,seat)=>{where[person]=seat;});let swaps=0;for(let seat=0;seat<seats.length;seat+=2){const partner=seats[seat]^1;if(seats[seat+1]!==partner){const other=where[partner];seats[other]=seats[seat+1];where[seats[other]]=other;seats[seat+1]=partner;where[partner]=seat+1;swaps++;}}return swaps;
}
function minSwapsCouples(row) { return solve(row); }
module.exports=solve;
module.exports.minSwapsCouples=minSwapsCouples;
