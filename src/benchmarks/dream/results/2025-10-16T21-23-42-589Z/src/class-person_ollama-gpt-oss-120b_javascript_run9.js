export default class Person {
  constructor(name, age, email) {
    this.name = name;
    this.age = age;
    this.email = email;
  }

  getInfo() {
    return `${this.name} (${this.age}) <${this.email}>`;
  }
}
