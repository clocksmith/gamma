/**
 * Mock LLM Client for testing without API keys
 * Generates deterministic responses based on task type
 */

export class MockLLMClient {
  constructor(providers) {
    this.providers = providers;
  }

  /**
   * Generate a mock response based on the task
   */
  async complete(provider, prompt) {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500 + Math.random() * 1000));

    // Generate response based on prompt content
    let content = '';

    if (prompt.includes('fibonacci')) {
      content = this.generateFibonacci(prompt);
    } else if (prompt.includes('filter') || prompt.includes('array')) {
      content = this.generateArrayFilter(prompt);
    } else if (prompt.includes('Person') || prompt.includes('class')) {
      content = this.generatePersonClass(prompt);
    } else if (prompt.includes('counter')) {
      content = this.generateCounter(prompt);
    } else {
      content = this.generateGenericResponse(prompt);
    }

    return {
      content,
      model: provider.model,
      usage: {
        input_tokens: Math.floor(prompt.length / 4),
        output_tokens: Math.floor(content.length / 4),
        total_tokens: Math.floor((prompt.length + content.length) / 4)
      }
    };
  }

  generateFibonacci(prompt) {
    const isTS = prompt.toLowerCase().includes('typescript');
    const isJSDoc = prompt.toLowerCase().includes('jsdoc');

    if (isTS) {
      return `export function fibonacci(n: number): number {
  if (n <= 1) return n;
  let a = 0, b = 1;
  for (let i = 2; i <= n; i++) {
    [a, b] = [b, a + b];
  }
  return b;
}`;
    } else if (isJSDoc) {
      return `/**
 * Calculate the nth Fibonacci number
 * @param {number} n - The position in the Fibonacci sequence
 * @returns {number} The Fibonacci number at position n
 */
export function fibonacci(n) {
  if (n <= 1) return n;
  let a = 0, b = 1;
  for (let i = 2; i <= n; i++) {
    [a, b] = [b, a + b];
  }
  return b;
}`;
    } else {
      return `export function fibonacci(n) {
  if (n <= 1) return n;
  let a = 0, b = 1;
  for (let i = 2; i <= n; i++) {
    [a, b] = [b, a + b];
  }
  return b;
}`;
    }
  }

  generateArrayFilter(prompt) {
    const isTS = prompt.toLowerCase().includes('typescript');
    const isJSDoc = prompt.toLowerCase().includes('jsdoc');

    if (isTS) {
      return `export function customFilter<T>(
  array: T[],
  predicate: (item: T, index: number) => boolean
): T[] {
  const result: T[] = [];
  for (let i = 0; i < array.length; i++) {
    if (predicate(array[i], i)) {
      result.push(array[i]);
    }
  }
  return result;
}`;
    } else if (isJSDoc) {
      return `/**
 * Filter array elements based on a predicate function
 * @template T
 * @param {T[]} array - The array to filter
 * @param {(item: T, index: number) => boolean} predicate - Filter function
 * @returns {T[]} Filtered array
 */
export function customFilter(array, predicate) {
  const result = [];
  for (let i = 0; i < array.length; i++) {
    if (predicate(array[i], i)) {
      result.push(array[i]);
    }
  }
  return result;
}`;
    } else {
      return `export function customFilter(array, predicate) {
  const result = [];
  for (let i = 0; i < array.length; i++) {
    if (predicate(array[i], i)) {
      result.push(array[i]);
    }
  }
  return result;
}`;
    }
  }

  generatePersonClass(prompt) {
    const isTS = prompt.toLowerCase().includes('typescript');
    const isJSDoc = prompt.toLowerCase().includes('jsdoc');

    if (isTS) {
      return `export interface IPerson {
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
    return \`Name: \${this.name}, Age: \${this.age}, Email: \${this.email}\`;
  }
}`;
    } else if (isJSDoc) {
      return `/**
 * @typedef {Object} PersonType
 * @property {string} name
 * @property {number} age
 * @property {string} email
 * @property {() => string} getInfo
 */

/**
 * @class
 */
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
   * @returns {string}
   */
  getInfo() {
    return \`Name: \${this.name}, Age: \${this.age}, Email: \${this.email}\`;
  }
}`;
    } else {
      return `export class Person {
  constructor(name, age, email) {
    this.name = name;
    this.age = age;
    this.email = email;
  }

  getInfo() {
    return \`Name: \${this.name}, Age: \${this.age}, Email: \${this.email}\`;
  }
}`;
    }
  }

  generateCounter(prompt) {
    if (prompt.includes('HTML') || prompt.includes('html') || prompt.includes('vanilla-web')) {
      return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Counter</title>
  <style>
    body {
      font-family: system-ui, -apple-system, sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      margin: 0;
      background: #f5f5f5;
    }
    .counter {
      background: white;
      padding: 2rem;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      text-align: center;
    }
    .count {
      font-size: 3rem;
      font-weight: bold;
      color: #333;
      margin: 1rem 0;
    }
    .buttons {
      display: flex;
      gap: 1rem;
      justify-content: center;
    }
    button {
      padding: 0.75rem 1.5rem;
      font-size: 1.25rem;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      background: #007bff;
      color: white;
      transition: background 0.2s;
    }
    button:hover {
      background: #0056b3;
    }
  </style>
</head>
<body>
  <div class="counter">
    <h1>Counter</h1>
    <div class="count" id="count">0</div>
    <div class="buttons">
      <button id="decrement">-</button>
      <button id="increment">+</button>
    </div>
  </div>

  <script>
    let count = 0;
    const countEl = document.getElementById('count');
    const incrementBtn = document.getElementById('increment');
    const decrementBtn = document.getElementById('decrement');

    function updateDisplay() {
      countEl.textContent = count;
    }

    incrementBtn.addEventListener('click', () => {
      count++;
      updateDisplay();
    });

    decrementBtn.addEventListener('click', () => {
      count--;
      updateDisplay();
    });
  </script>
</body>
</html>`;
    }

    return `export class Counter {
  constructor() {
    this.count = 0;
  }

  increment() {
    this.count++;
  }

  decrement() {
    this.count--;
  }

  getCount() {
    return this.count;
  }
}`;
  }

  generateGenericResponse(prompt) {
    return `// Mock response for: ${prompt.substring(0, 100)}...
// This is a simulated LLM response for testing purposes.
// To get real results, configure API keys in .env

export function mockImplementation() {
  console.log('This is a mock implementation');
  return { success: true, message: 'Mock implementation' };
}`;
  }
}
