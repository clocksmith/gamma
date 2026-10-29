"use strict";
class ParkingSystem {
 constructor(big,medium,small){this.remaining=[big,medium,small];}
 addCar(carType){const index=carType-1;if(this.remaining[index]===0)return false;this.remaining[index]--;return true;}
}
module.exports={ParkingSystem};
