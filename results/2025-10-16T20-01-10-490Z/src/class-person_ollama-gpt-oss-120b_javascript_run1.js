export class Person {
  constructor(name, age, email) {
    this.name = name;
    this.age = age;
    this.email = email;
  }

  getInfo() {
    return `Name: ${this.name}, Age: ${this.age}, Email: ${this.email}`;
  }
}