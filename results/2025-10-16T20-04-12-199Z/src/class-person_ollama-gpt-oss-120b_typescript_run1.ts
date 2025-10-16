export interface IPerson {
  name: string;
  age: number;
  email: string;
}

export class Person implements IPerson {
  constructor(
    public name: string,
    public age: number,
    public email: string
  ) {}

  getInfo(): string {
    return `${this.name} (${this.age}) – ${this.email}`;
  }
}
