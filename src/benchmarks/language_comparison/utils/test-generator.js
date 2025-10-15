/**
 * Property-Based Test Generator
 * Automatically generates test cases and benchmarks
 */

export class TestGenerator {
  /**
   * Generate property-based tests for a function
   */
  static generatePropertyTests(functionSignature, properties = []) {
    const tests = [];

    // Default properties if none specified
    if (properties.length === 0) {
      properties = [
        'idempotence',
        'commutativity',
        'associativity',
        'identity',
        'nullHandling',
        'boundaryConditions'
      ];
    }

    for (const property of properties) {
      const testCase = this.generateTestForProperty(functionSignature, property);
      if (testCase) {
        tests.push(testCase);
      }
    }

    return tests;
  }

  /**
   * Generate test for a specific property
   */
  static generateTestForProperty(functionSignature, property) {
    const generators = {
      idempotence: this.generateIdempotenceTest,
      commutativity: this.generateCommutativityTest,
      associativity: this.generateAssociativityTest,
      identity: this.generateIdentityTest,
      nullHandling: this.generateNullHandlingTest,
      boundaryConditions: this.generateBoundaryTest,
      typeInvariance: this.generateTypeInvarianceTest,
      monotonicality: this.generateMonotonicityTest
    };

    const generator = generators[property];
    return generator ? generator.call(this, functionSignature) : null;
  }

  /**
   * Generate idempotence test (f(f(x)) === f(x))
   */
  static generateIdempotenceTest(fn) {
    return {
      name: 'idempotence',
      description: `${fn.name} should be idempotent`,
      test: `
        const input = ${this.generateRandomInput(fn.params[0])};
        const result1 = ${fn.name}(input);
        const result2 = ${fn.name}(result1);
        console.assert(JSON.stringify(result1) === JSON.stringify(result2),
          'Function should be idempotent: f(f(x)) === f(x)');
      `
    };
  }

  /**
   * Generate commutativity test (f(a, b) === f(b, a))
   */
  static generateCommutativityTest(fn) {
    if (fn.params.length < 2) return null;

    return {
      name: 'commutativity',
      description: `${fn.name} should be commutative`,
      test: `
        const a = ${this.generateRandomInput(fn.params[0])};
        const b = ${this.generateRandomInput(fn.params[1])};
        const result1 = ${fn.name}(a, b);
        const result2 = ${fn.name}(b, a);
        console.assert(JSON.stringify(result1) === JSON.stringify(result2),
          'Function should be commutative: f(a,b) === f(b,a)');
      `
    };
  }

  /**
   * Generate associativity test (f(f(a, b), c) === f(a, f(b, c)))
   */
  static generateAssociativityTest(fn) {
    if (fn.params.length < 2) return null;

    return {
      name: 'associativity',
      description: `${fn.name} should be associative`,
      test: `
        const a = ${this.generateRandomInput(fn.params[0])};
        const b = ${this.generateRandomInput(fn.params[1])};
        const c = ${this.generateRandomInput(fn.params[1])};
        const result1 = ${fn.name}(${fn.name}(a, b), c);
        const result2 = ${fn.name}(a, ${fn.name}(b, c));
        console.assert(JSON.stringify(result1) === JSON.stringify(result2),
          'Function should be associative');
      `
    };
  }

  /**
   * Generate identity test (f(x, identity) === x)
   */
  static generateIdentityTest(fn) {
    return {
      name: 'identity',
      description: `${fn.name} should have identity element`,
      test: `
        const input = ${this.generateRandomInput(fn.params[0])};
        const identity = ${this.generateIdentityValue(fn.params[0])};
        const result = ${fn.name}(input, identity);
        console.assert(JSON.stringify(result) === JSON.stringify(input) ||
                      JSON.stringify(result) === JSON.stringify(identity),
          'Function should have identity element');
      `
    };
  }

  /**
   * Generate null/undefined handling test
   */
  static generateNullHandlingTest(fn) {
    return {
      name: 'nullHandling',
      description: `${fn.name} should handle null/undefined gracefully`,
      test: `
        try {
          const result1 = ${fn.name}(null);
          const result2 = ${fn.name}(undefined);
          // If it doesn't throw, it should return something reasonable
          console.assert(result1 !== undefined || result2 !== undefined,
            'Function should handle null/undefined');
        } catch (e) {
          // Throwing is also acceptable
          console.assert(e instanceof Error, 'Should throw proper Error');
        }
      `
    };
  }

  /**
   * Generate boundary condition tests
   */
  static generateBoundaryTest(fn) {
    const param = fn.params[0];
    const boundaries = this.getBoundaryValues(param.type);

    return {
      name: 'boundaryConditions',
      description: `${fn.name} should handle boundary conditions`,
      test: `
        const boundaries = ${JSON.stringify(boundaries)};
        for (const boundary of boundaries) {
          try {
            const result = ${fn.name}(boundary);
            console.assert(result !== undefined, \`Should handle boundary: \${boundary}\`);
          } catch (e) {
            // Some boundaries may throw, which is acceptable
          }
        }
      `
    };
  }

  /**
   * Generate type invariance test
   */
  static generateTypeInvarianceTest(fn) {
    return {
      name: 'typeInvariance',
      description: `${fn.name} output type should be consistent`,
      test: `
        const inputs = [
          ${this.generateRandomInput(fn.params[0])},
          ${this.generateRandomInput(fn.params[0])},
          ${this.generateRandomInput(fn.params[0])}
        ];

        const types = inputs.map(input => {
          try {
            const result = ${fn.name}(input);
            return typeof result;
          } catch {
            return 'error';
          }
        }).filter(t => t !== 'error');

        const uniqueTypes = new Set(types);
        console.assert(uniqueTypes.size <= 1,
          'Output type should be consistent across inputs');
      `
    };
  }

  /**
   * Generate monotonicity test (for ordered types)
   */
  static generateMonotonicityTest(fn) {
    return {
      name: 'monotonicity',
      description: `${fn.name} should be monotonic`,
      test: `
        const values = [1, 2, 3, 5, 10, 20, 50, 100];
        const results = values.map(v => {
          try {
            return ${fn.name}(v);
          } catch {
            return null;
          }
        }).filter(r => r !== null && typeof r === 'number');

        let isMonotonic = true;
        for (let i = 1; i < results.length; i++) {
          if (results[i] < results[i-1]) {
            isMonotonic = false;
            break;
          }
        }

        if (results.length >= 2) {
          console.assert(isMonotonic || results.every((r, i, arr) =>
            i === 0 || r <= arr[i-1]), 'Function should be monotonic');
        }
      `
    };
  }

  /**
   * Generate random input based on type
   */
  static generateRandomInput(param) {
    const type = param?.type || 'any';

    const generators = {
      'number': () => Math.floor(Math.random() * 100),
      'string': () => `'test${Math.floor(Math.random() * 100)}'`,
      'boolean': () => Math.random() > 0.5,
      'array': () => `[${Array(5).fill(0).map(() => Math.floor(Math.random() * 10)).join(',')}]`,
      'object': () => `{ x: ${Math.floor(Math.random() * 100)}, y: ${Math.floor(Math.random() * 100)} }`,
      'any': () => generators.number()
    };

    return generators[type]?.() || generators['any']();
  }

  /**
   * Generate identity value for type
   */
  static generateIdentityValue(param) {
    const type = param?.type || 'any';

    const identities = {
      'number': 0,
      'string': "''",
      'boolean': false,
      'array': '[]',
      'object': '{}'
    };

    return identities[type] || 'null';
  }

  /**
   * Get boundary values for type
   */
  static getBoundaryValues(type) {
    const boundaries = {
      'number': [0, 1, -1, Number.MAX_SAFE_INTEGER, Number.MIN_SAFE_INTEGER, Infinity, -Infinity, NaN],
      'string': ['', ' ', 'a', 'A', '0', '\\n', '\\t'],
      'array': [[], [0], [1, 2, 3], Array(1000).fill(0)],
      'boolean': [true, false],
      'object': [{}, { a: 1 }, { a: { b: { c: 1 } } }]
    };

    return boundaries[type] || [null, undefined, 0, '', [], {}];
  }

  /**
   * Generate fuzzing test cases
   */
  static generateFuzzingTests(fn, count = 100) {
    const tests = [];

    for (let i = 0; i < count; i++) {
      tests.push({
        name: `fuzz_${i}`,
        description: `Fuzzing test ${i}`,
        test: `
          try {
            const input = ${this.generateRandomFuzzInput()};
            const result = ${fn.name}(input);
            // Function should not crash
            console.assert(true, 'Fuzzing test passed');
          } catch (e) {
            // Errors are acceptable, crashes are not
            console.assert(e instanceof Error, 'Should throw proper Error');
          }
        `
      });
    }

    return tests;
  }

  /**
   * Generate random fuzzing input (potentially invalid)
   */
  static generateRandomFuzzInput() {
    const fuzzTypes = [
      'null',
      'undefined',
      'NaN',
      'Infinity',
      '-Infinity',
      '{}',
      '[]',
      '"\\x00"',
      '"\\uFFFF"',
      '{ toString: () => { throw new Error(); } }',
      '{ valueOf: () => { throw new Error(); } }',
      'new Proxy({}, { get: () => { throw new Error(); } })',
      '""',
      '0',
      '-1',
      '1e308',
      'Symbol("test")',
      'function() {}',
      '/regex/'
    ];

    return fuzzTypes[Math.floor(Math.random() * fuzzTypes.length)];
  }

  /**
   * Generate benchmark task from template
   */
  static generateBenchmarkTask(options) {
    const {
      name,
      description,
      category = 'generated',
      difficulty = 'medium',
      functionSignature,
      variants = ['typescript', 'javascript', 'javascript-jsdoc']
    } = options;

    const task = {
      name: name || `generated_${Date.now()}`,
      description: description || 'Auto-generated benchmark task',
      category,
      difficulty,
      variants: {},
      testCases: this.generatePropertyTests(functionSignature).map(t => ({ test: t.test })),
      requirements: ['function', functionSignature.name, 'export']
    };

    // Generate prompts for each variant
    for (const variant of variants) {
      task.variants[variant] = this.generatePromptForVariant(functionSignature, variant);
    }

    return task;
  }

  /**
   * Generate prompt for specific variant
   */
  static generatePromptForVariant(fn, variant) {
    const paramList = fn.params.map(p => `${p.name}: ${p.type}`).join(', ');

    const prompts = {
      typescript: `Write a TypeScript function called \`${fn.name}\` that takes ${fn.params.length} parameter(s): ${paramList}. ${fn.description || ''} Include proper type annotations and export the function.`,

      javascript: `Write a JavaScript function called \`${fn.name}\` that takes ${fn.params.length} parameter(s): ${fn.params.map(p => p.name).join(', ')}. ${fn.description || ''} Export the function.`,

      'javascript-jsdoc': `Write a JavaScript function called \`${fn.name}\` that takes ${fn.params.length} parameter(s): ${fn.params.map(p => p.name).join(', ')}. ${fn.description || ''} Include JSDoc type annotations with @param and @return tags. Export the function.`
    };

    return prompts[variant] || prompts.javascript;
  }

  /**
   * Generate stress test scenarios
   */
  static generateStressTests(fn) {
    return [
      {
        name: 'large_input',
        description: 'Test with large input',
        test: `
          const largeInput = Array(10000).fill(0).map((_, i) => i);
          const start = Date.now();
          const result = ${fn.name}(largeInput);
          const duration = Date.now() - start;
          console.assert(duration < 5000, 'Should handle large input within 5 seconds');
        `
      },
      {
        name: 'repeated_calls',
        description: 'Test repeated calls',
        test: `
          const input = ${this.generateRandomInput(fn.params[0])};
          const start = Date.now();
          for (let i = 0; i < 1000; i++) {
            ${fn.name}(input);
          }
          const duration = Date.now() - start;
          console.assert(duration < 10000, 'Should handle 1000 calls within 10 seconds');
        `
      },
      {
        name: 'memory_leak',
        description: 'Test for memory leaks',
        test: `
          if (typeof process !== 'undefined' && process.memoryUsage) {
            const before = process.memoryUsage().heapUsed;
            for (let i = 0; i < 10000; i++) {
              ${fn.name}(${this.generateRandomInput(fn.params[0])});
            }
            const after = process.memoryUsage().heapUsed;
            const increase = (after - before) / 1024 / 1024; // MB
            console.assert(increase < 100, \`Memory increase should be < 100MB, got \${increase.toFixed(2)}MB\`);
          }
        `
      }
    ];
  }
}
