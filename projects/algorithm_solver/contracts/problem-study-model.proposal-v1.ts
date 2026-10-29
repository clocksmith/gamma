/**
 * Compatibility pointer for the earlier proposal. The single maintained schema
 * authority is projects/problem_catalogue/schema.py plus graphs.py; both runtime
 * JSON Schema and TypeScript are generated there. Existing consumers are unchanged.
 */
export * from '../../problem_catalogue/schema.v1';
