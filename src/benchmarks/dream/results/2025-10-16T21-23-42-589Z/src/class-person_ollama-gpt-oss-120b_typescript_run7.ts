export interface IPerson {
  name: string;
  age: number;
  email: string;
  getInfo(): string;
}

export class Person implements IPerson {
  constructor(
    public name: string,
    public age: number,
    public email: string
  ) {}

  getInfo(): string {
    return `Name: ${this.name}, Age: ${this.age}, Email: ${this.email}`;
  }
}
