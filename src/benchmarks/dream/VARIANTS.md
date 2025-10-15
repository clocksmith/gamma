# Language Variants Guide

This document explains each language variant tested in the benchmark suite and what makes them unique.

## Core Variants

### 1. TypeScript (`typescript`)

Pure TypeScript with full type annotations.

**Characteristics:**
- Full type safety
- Interfaces and type aliases
- Generic types
- Strict type checking
- No runtime overhead for types
- Best IDE support

**Example:**
```typescript
interface User {
  id: number;
  name: string;
  email: string;
}

function getUser(id: number): Promise<User> {
  return fetch(`/api/users/${id}`).then(r => r.json());
}
```

**Use Cases:** Backend services, large applications, team projects

---

### 2. JavaScript (`javascript`)

Plain JavaScript with no type annotations.

**Characteristics:**
- No type system
- Runtime-only error checking
- Flexible and dynamic
- Smaller code size
- Faster to write initially
- Less tooling required

**Example:**
```javascript
function getUser(id) {
  return fetch(`/api/users/${id}`).then(r => r.json());
}
```

**Use Cases:** Small scripts, prototypes, simple applications

---

### 3. JavaScript with JSDoc (`javascript-jsdoc`)

JavaScript with comprehensive JSDoc type annotations.

**Characteristics:**
- Type hints in comments
- TypeScript-like checking without compilation
- IDE autocomplete support
- Runtime overhead: none
- Can enable TypeScript checking via `// @ts-check`
- Good middle ground

**Example:**
```javascript
/**
 * @typedef {Object} User
 * @property {number} id
 * @property {string} name
 * @property {string} email
 */

/**
 * @param {number} id
 * @returns {Promise<User>}
 */
function getUser(id) {
  return fetch(`/api/users/${id}`).then(r => r.json());
}
```

**Use Cases:** Existing JavaScript projects wanting types, gradual migration

---

## Web Variants

### 4. JavaScript Vanilla Web (`javascript-vanilla-web`)

JavaScript with HTML, CSS, and vanilla Web APIs.

**Characteristics:**
- No frameworks or libraries
- Direct DOM manipulation
- Standard Web APIs only
- Complete HTML/CSS/JS implementation
- Single file or simple structure
- Maximum compatibility

**Example:**
```html
<!DOCTYPE html>
<html>
<head>
  <style>
    .container { padding: 20px; }
    button { padding: 10px 20px; }
  </style>
</head>
<body>
  <div class="container">
    <h1 id="title">Counter: <span id="count">0</span></h1>
    <button id="increment">+</button>
    <button id="decrement">-</button>
  </div>

  <script>
    let count = 0;
    const countEl = document.getElementById('count');

    document.getElementById('increment').addEventListener('click', () => {
      count++;
      countEl.textContent = count;
    });

    document.getElementById('decrement').addEventListener('click', () => {
      count--;
      countEl.textContent = count;
    });
  </script>
</body>
</html>
```

**Use Cases:** Simple web pages, learning, no-build setups

---

### 5. JavaScript Vanilla Web with JSDoc (`javascript-vanilla-web-jsdoc`)

Same as vanilla web, but with complete JSDoc type annotations.

**Characteristics:**
- All features of vanilla web
- JSDoc type annotations throughout
- Better IDE support
- Type checking available
- Self-documenting code

**Example:**
```html
<script>
/**
 * @typedef {Object} CounterState
 * @property {number} count
 */

/** @type {CounterState} */
const state = { count: 0 };

/**
 * Updates the counter display
 * @param {number} newCount
 * @returns {void}
 */
function updateDisplay(newCount) {
  const countEl = document.getElementById('count');
  if (countEl) {
    countEl.textContent = newCount.toString();
  }
}

// Event handlers...
</script>
```

**Use Cases:** Documented vanilla projects, teaching, team collaboration

---

### 6. TypeScript Vanilla Web (`typescript-vanilla-web`)

TypeScript with vanilla Web APIs (no frameworks).

**Characteristics:**
- Full TypeScript type safety
- Vanilla DOM APIs
- Proper event typing
- HTMLElement type assertions
- Compiled to JavaScript
- Best of both worlds

**Example:**
```typescript
// counter.ts
interface CounterState {
  count: number;
}

class Counter {
  private state: CounterState = { count: 0 };
  private countElement: HTMLElement;

  constructor(counterId: string) {
    const element = document.getElementById(counterId);
    if (!element) throw new Error(`Element ${counterId} not found`);
    this.countElement = element;
  }

  increment(): void {
    this.state.count++;
    this.render();
  }

  private render(): void {
    this.countElement.textContent = this.state.count.toString();
  }
}

// Initialize
const counter = new Counter('count');
document.getElementById('increment')?.addEventListener('click', () => {
  counter.increment();
});
```

**HTML:**
```html
<!DOCTYPE html>
<html>
<head>
  <script src="counter.js"></script>
</head>
<body>
  <div id="count">0</div>
  <button id="increment">+</button>
</body>
</html>
```

**Use Cases:** Type-safe web apps without frameworks, modern vanilla projects

---

### 7. TypeScript React (`typescript-react`)

React with TypeScript (minimal dependencies).

**Characteristics:**
- React components
- TypeScript types for props, state, hooks
- JSX/TSX syntax
- Modern React patterns (hooks)
- Minimal external dependencies
- Type-safe component props

**Example:**
```tsx
// Counter.tsx
interface CounterProps {
  initialCount?: number;
  onCountChange?: (count: number) => void;
}

export const Counter: React.FC<CounterProps> = ({
  initialCount = 0,
  onCountChange
}) => {
  const [count, setCount] = React.useState(initialCount);

  const increment = () => {
    const newCount = count + 1;
    setCount(newCount);
    onCountChange?.(newCount);
  };

  const decrement = () => {
    const newCount = count - 1;
    setCount(newCount);
    onCountChange?.(newCount);
  };

  return (
    <div>
      <h1>Counter: {count}</h1>
      <button onClick={increment}>+</button>
      <button onClick={decrement}>-</button>
    </div>
  );
};

// Usage
<Counter initialCount={5} onCountChange={(c) => console.log(c)} />
```

**Use Cases:** Modern web applications, complex UIs, team projects

---

## Comparison Matrix

| Variant | Type Safety | Compile Step | Runtime Types | Framework | Complexity |
|---------|-------------|--------------|---------------|-----------|------------|
| TypeScript | ✅ Full | ✅ Yes | ❌ No | ❌ No | Medium |
| JavaScript | ❌ None | ❌ No | ❌ No | ❌ No | Low |
| JS + JSDoc | ⚠️ Optional | ❌ No | ❌ No | ❌ No | Low-Med |
| JS Vanilla Web | ❌ None | ❌ No | ❌ No | ❌ No | Low |
| JS Vanilla Web + JSDoc | ⚠️ Optional | ❌ No | ❌ No | ❌ No | Low-Med |
| TS Vanilla Web | ✅ Full | ✅ Yes | ❌ No | ❌ No | Medium |
| TS React | ✅ Full | ✅ Yes | ❌ No | ✅ React | High |

---

## Which Variant Should LLMs Excel At?

### Expected Strengths:

1. **TypeScript**: Should produce the most correct code due to compile-time checks
2. **JavaScript + JSDoc**: Good balance between flexibility and type safety
3. **TypeScript React**: Type safety helps with complex component hierarchies
4. **Vanilla Web variants**: More boilerplate but straightforward

### Expected Challenges:

1. **Plain JavaScript**: Easier to introduce type-related bugs
2. **Vanilla Web**: More manual DOM manipulation code
3. **TypeScript React**: Complex generic types can be tricky

---

## Benchmark Focus Areas

### Type Safety
- How well does each variant catch errors?
- Does type information help LLMs produce correct code?

### Code Quality
- Which variant produces the most maintainable code?
- How do comments/JSDoc affect code quality?

### Completeness
- Are typed variants more complete?
- Do frameworks help or hinder completeness?

### Performance (LLM Efficiency)
- Which variant requires fewer tokens?
- Does type information speed up or slow down generation?

### Practical Usability
- Which code would developers prefer to maintain?
- How much boilerplate is required?

---

## Adding New Variants

To add a new variant:

1. Update `benchmark/config.js`:
   ```javascript
   variants: [
     // ... existing variants
     'your-new-variant'
   ]
   ```

2. Add variant prompts to task JSON files:
   ```json
   {
     "variants": {
       "your-new-variant": "Prompt for this variant..."
     }
   }
   ```

3. Update evaluation logic if needed in `evaluator/evaluator.js`

4. Document the variant in this file

---

## Best Practices for Fair Comparison

1. **Keep prompts similar**: Only change what's necessary for the variant
2. **Same functionality**: All variants should produce identical behavior
3. **Equal detail**: Don't give one variant more detailed instructions
4. **Fair dependencies**: Allow necessary tooling for each variant
5. **Realistic constraints**: Match real-world usage patterns

---

## Resources

- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/)
- [JSDoc Reference](https://jsdoc.app/)
- [MDN Web APIs](https://developer.mozilla.org/en-US/docs/Web/API)
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)
