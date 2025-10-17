export class Person {
  /**
   * @param {string} name
   * @param {number} age
   * @param {string} email
   */
  constructor(name, age, email) {
    this.name = name;
    this.age = age;
    this.email = email;
  }

  /**
   * Returns a formatted string with the person's details.
   * @returns {string}
   */
  getInfo() {
    return `${this.name}, ${this.age} years old, Email: ${this.email}`;
  }
}
