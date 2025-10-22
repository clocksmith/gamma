#!/usr/bin/env node

/**
 * LLM TypeScript/JavaScript Benchmark Suite
 * Streamlined CLI for comparing JavaScript vs TypeScript generation quality.
 */

import { BenchmarkRunner } from './runner/benchmark-runner.js';
import { BenchmarkConfig } from './config.js';
import { PresetManager } from './presets.js';

const DEFAULT_VARIANT_PAIR = ['javascript', 'typescript'];
const ALL_VARIANTS = [...BenchmarkConfig.variants];
const PROVIDER_MAP = new Map(BenchmarkConfig.providers.map(provider => [provider.name, provider]));
const PROVIDER_NAMES = BenchmarkConfig.providers.map(provider => provider.name);

const CLI_PRESETS = {
  basic: {
    description: 'Foundational coding tasks comparing JS vs TS (no browser)',
    categories: ['1-foundations'],
    variants: DEFAULT_VARIANT_PAIR,
    includeBrowser: false,
    runs: 1,
    providers: ['ollama-gpt-oss-120b']
  },
  extended: {
    description: 'Foundations plus larger scripting and backend-style tasks',
    categories: ['1-foundations', '2-scripting-and-automation', '3-server-side-development'],
    variants: DEFAULT_VARIANT_PAIR,
    includeBrowser: false,
    runs: 1,
    providers: ['ollama-gpt-oss-120b', 'ollama-qwen3-30b']
  },
  ui: {
    description: 'Adds web/React tasks for UI comparisons (requires Playwright)',
    categories: ['1-foundations', '4-web-fundamentals', '5-react-component-library'],
    variants: [
      'javascript-no-comments',
      'typescript-no-comments',
      'javascript-vanilla-web-jsdoc',
      'typescript-react-tsdoc'
    ],
    includeBrowser: true,
    runs: 1,
    providers: ['ollama-gpt-oss-120b']
  },
  full: {
    description: 'Full DREAM benchmark suite across all categories and variants',
    categories: Object.keys(BenchmarkConfig.categories),
    variants: [...BenchmarkConfig.variants],
    includeBrowser: true
  }
};

const PRESET_ALIASES = {
  default: 'basic',
  basic: 'basic',
  quick: 'basic',
  compare: 'basic',
  'compare-basic': 'basic',
  extended: 'extended',
  'compare-extended': 'extended',
  backend: 'extended',
  advanced: 'extended',
  ui: 'ui',
  browser: 'ui',
  frontend: 'ui',
  web: 'ui',
  all: 'full',
  full: 'full',
  everything: 'full'
};

const VARIANT_GROUPS = buildVariantGroups();
const VARIANT_ALIASES = {
  default: 'core',
  compare: 'core',
  language: 'core',
  javascript: 'js',
  js: 'js',
  typescript: 'ts',
  ts: 'ts',
  doc: 'docs',
  docs: 'docs',
  react: 'react',
  web: 'web'
};

const CATEGORY_DATA = {
  '1-foundations': {
    label: '1. Foundations',
    description: 'Core coding fundamentals',
    aliases: ['1', 'foundations', 'fundamentals', 'basics', 'core', 'simple', 'starter']
  },
  '2-scripting-and-automation': {
    label: '2. Scripting & Automation',
    description: 'CLI and automation tasks',
    aliases: ['2', 'automation', 'scripting', 'scripts', 'cli']
  },
  '3-server-side-development': {
    label: '3. Server-side Development',
    description: 'Backend and API work',
    aliases: ['3', 'server', 'backend', 'api', 'services']
  },
  '4-web-fundamentals': {
    label: '4. Web Fundamentals',
    description: 'Browser DOM manipulation',
    aliases: ['4', 'web', 'frontend', 'dom']
  },
  '5-react-component-library': {
    label: '5. React Component Library',
    description: 'React components and UI',
    aliases: ['5', 'react', 'components', 'ui', 'library']
  },
  '6-full-stack-applications': {
    label: '6. Full-stack Applications',
    description: 'End-to-end application workflows',
    aliases: ['6', 'fullstack', 'full-stack', 'applications', 'apps']
  },
  '7-debugging-and-maintenance': {
    label: '7. Debugging & Maintenance',
    description: 'Bug fixing and maintenance',
    aliases: ['7', 'debugging', 'maintenance', 'bug', 'bugs']
  }
};

const CATEGORY_GROUPS = {
  basics: ['1-foundations'],
  fundamentals: ['1-foundations'],
  automation: ['2-scripting-and-automation'],
  scripting: ['2-scripting-and-automation'],
  backend: ['2-scripting-and-automation', '3-server-side-development'],
  server: ['3-server-side-development'],
  frontend: ['4-web-fundamentals', '5-react-component-library'],
  web: ['4-web-fundamentals'],
  ui: ['5-react-component-library'],
  react: ['5-react-component-library'],
  fullstack: ['6-full-stack-applications'],
  maintenance: ['7-debugging-and-maintenance'],
  advanced: ['3-server-side-development', '6-full-stack-applications', '7-debugging-and-maintenance'],
  all: Object.keys(CATEGORY_DATA)
};

const CATEGORY_LOOKUP = buildCategoryLookup();
const BROWSER_CATEGORIES = new Set(['4-web-fundamentals', '5-react-component-library']);
const PROVIDER_LOOKUP = buildProviderLookup();

async function main() {
  const args = process.argv.slice(2);
  const state = createInitialState();

  try {
    parseArgs(args, state);
  } catch (error) {
    console.error(`Error: ${error.message}`);
    process.exit(1);
  }

  if (state.help) {
    printHelp();
    return;
  }

  let listed = false;
  if (state.listPresets) {
    listPresets();
    listed = true;
  }
  if (state.listProviders) {
    listProviders();
    listed = true;
  }
  if (state.listVariants) {
    listVariants();
    listed = true;
  }
  if (state.listCategories) {
    listCategories();
    listed = true;
  }
  if (state.listTasks) {
    await listTasks();
    listed = true;
  }
  if (listed && !state.runAfterList) {
    return;
  }

  let plan;
  try {
    plan = finalizePlan(state);
  } catch (error) {
    console.error(`Error: ${error.message}`);
    process.exit(1);
  }

  const config = cloneConfig(BenchmarkConfig);
  for (const presetName of state.legacyPresets) {
    try {
      const applied = PresetManager.applyPreset(config, presetName);
      Object.assign(config, applied);
    } catch (error) {
      console.warn(`⚠️  Failed to apply preset "${presetName}": ${error.message}`);
    }
  }

  ensureProviderObjects(config);

  if (state.runs != null) {
    config.runs = state.runs;
  }
  if (state.timeout != null) {
    config.timeout = state.timeout;
  }

  // Determine which temperatures to test
  let temperatures = [];
  if (plan.temperatures.length > 0) {
    temperatures = plan.temperatures;
  } else if (plan.temperature != null) {
    temperatures = [plan.temperature];
  } else {
    temperatures = [1.0]; // Default temperature
  }

  const providerLookup = new Map(config.providers.map(provider => [provider.name, provider]));
  const selectedProviderObjects = plan.providers
    .map(name => providerLookup.get(name))
    .filter(Boolean);

  // Use state.dryRun directly (defaults to false = live mode)
  const dryRun = state.dryRun;

  // Only warn if trying to use live mode without credentials
  if (!dryRun) {
    const hasCredentials = selectedProviderObjects.some(provider => provider.apiKey || provider.baseUrl);
    if (!hasCredentials) {
      console.warn('⚠️  Warning: No API keys or Ollama base URL detected for selected providers.');
      console.warn('    Live mode will fail without proper configuration. Use --dry for mock responses.');
    }
  }

  config.dryRun = Boolean(dryRun);

  const filters = {
    providers: plan.providers,
    variants: plan.variants,
    categories: plan.categories,
    includeBrowser: state.includeBrowser
  };

  if (plan.tasks.length > 0) {
    filters.tasks = plan.tasks;
    if (plan.tasks.length === 1) {
      filters.taskName = plan.tasks[0];
    }
  }
  if (state.timeout) {
    filters.timeout = state.timeout;
  }

  if (plan.warnings.length > 0) {
    for (const warning of plan.warnings) {
      console.warn(`⚠️  ${warning}`);
    }
  }

  const presetSummary = state.presetSelections.length > 0
    ? state.presetSelections.map(item => item.source === 'auto' ? `${item.key} (default)` : item.key).join(', ')
    : 'custom';

  console.log('\n🧭  Benchmark plan');
  console.log(`  Preset(s):        ${presetSummary}`);
  console.log(`  Providers:        ${plan.providers.join(', ')}`);
  console.log(`  Variants:         ${plan.variants.join(', ')}`);
  console.log(`  Categories:       ${plan.categories.join(', ')}`);
  if (plan.tasks.length > 0) {
    console.log(`  Tasks:            ${plan.tasks.join(', ')}`);
  }
  console.log(`  Runs per combo:   ${config.runs}`);
  if (state.timeout) {
    console.log(`  Timeout override: ${state.timeout} ms`);
  }
  if (temperatures.length > 1) {
    console.log(`  Temperatures:     ${temperatures.join(', ')}`);
  } else if (temperatures[0] !== undefined) {
    console.log(`  Temperature:      ${temperatures[0]}`);
  }
  console.log(`  Browser tasks:    ${state.includeBrowser ? 'enabled' : 'skipped (use --include-browser to enable)'}`);
  console.log(`  Mode:             ${config.dryRun ? 'mock (use --dry flag to enable)' : 'live'}`);
  console.log('');

  try {
    if (config.dryRun) {
      console.log('🔬 MOCK MODE - Using simulated LLM responses\n');
    }

    // Run benchmark for each temperature value
    for (let tempIndex = 0; tempIndex < temperatures.length; tempIndex++) {
      const temp = temperatures[tempIndex];

      if (temperatures.length > 1) {
        console.log(`\n${'='.repeat(80)}`);
        console.log(`🌡️  Running with temperature: ${temp} (${tempIndex + 1}/${temperatures.length})`);
        console.log('='.repeat(80) + '\n');
      }

      // Set temperature for this run
      config.temperature = temp;
      const runner = new BenchmarkRunner(config);

      await runner.run(filters);
    }
  } catch (error) {
    console.error('Benchmark failed:', error.message || error);
    if (error.stack) {
      console.error(error.stack);
    }
    process.exit(1);
  }
}

function buildVariantGroups() {
  const groups = {};
  groups.all = [...ALL_VARIANTS];
  groups.core = [...DEFAULT_VARIANT_PAIR];
  groups.compare = groups.core;
  groups.js = ALL_VARIANTS.filter(variant => variant.includes('javascript'));
  groups.javascript = groups.js;
  groups.ts = ALL_VARIANTS.filter(variant => variant.includes('typescript'));
  groups.typescript = groups.ts;
  groups.docs = ALL_VARIANTS.filter(variant => variant.includes('jsdoc') || variant.includes('tsdoc'));
  groups.react = ALL_VARIANTS.filter(variant => variant.includes('react'));
  groups.web = ALL_VARIANTS.filter(variant => variant.includes('vanilla-web'));
  return groups;
}

function buildCategoryLookup() {
  const lookup = {};
  const add = (key, categories) => {
    const normalized = normalize(key);
    if (!lookup[normalized]) {
      lookup[normalized] = new Set();
    }
    for (const category of categories) {
      if (CATEGORY_DATA[category]) {
        lookup[normalized].add(category);
      }
    }
  };

  for (const [key, data] of Object.entries(CATEGORY_DATA)) {
    add(key, [key]);
    for (const alias of data.aliases) {
      add(alias, [key]);
    }
  }

  for (const [group, categories] of Object.entries(CATEGORY_GROUPS)) {
    add(group, categories);
  }

  return Object.fromEntries(
    Object.entries(lookup).map(([key, set]) => [key, Array.from(set)])
  );
}

function buildProviderLookup() {
  const lookup = {};
  const add = (key, names) => {
    const normalized = normalize(key);
    if (!lookup[normalized]) {
      lookup[normalized] = new Set();
    }
    for (const name of names) {
      if (PROVIDER_MAP.has(name)) {
        lookup[normalized].add(name);
      }
    }
  };

  add('all', PROVIDER_NAMES);

  for (const name of PROVIDER_NAMES) {
    add(name, [name]);
  }

  const localNames = PROVIDER_NAMES.filter(name => PROVIDER_MAP.get(name)?.baseUrl);
  if (localNames.length > 0) {
    add('local', localNames);
  }
  const cloudNames = PROVIDER_NAMES.filter(name => !PROVIDER_MAP.get(name)?.baseUrl);
  if (cloudNames.length > 0) {
    add('cloud', cloudNames);
    add('remote', cloudNames);
  }

  const openaiNames = PROVIDER_NAMES.filter(name => name.startsWith('openai'));
  if (openaiNames.length > 0) {
    add('openai', openaiNames);
  }
  const anthropicNames = PROVIDER_NAMES.filter(name => name.startsWith('anthropic'));
  if (anthropicNames.length > 0) {
    add('anthropic', anthropicNames);
  }
  const geminiNames = PROVIDER_NAMES.filter(name => name.startsWith('gemini') || name.startsWith('google'));
  if (geminiNames.length > 0) {
    add('gemini', geminiNames);
    add('google', geminiNames);
  }
  const ollamaNames = PROVIDER_NAMES.filter(name => name.startsWith('ollama'));
  if (ollamaNames.length > 0) {
    add('ollama', ollamaNames);
  }

  const recommended = [];
  for (const name of ['ollama-gpt-oss-120b', 'ollama-qwen3-30b', 'openai-gpt4']) {
    if (PROVIDER_MAP.has(name)) {
      recommended.push(name);
    }
  }
  if (recommended.length > 0) {
    add('recommended', recommended);
  }

  if (PROVIDER_MAP.has('openai-gpt4')) {
    add('gpt4', ['openai-gpt4']);
    add('gpt-4', ['openai-gpt4']);
  }
  if (PROVIDER_MAP.has('openai-gpt35')) {
    add('gpt35', ['openai-gpt35']);
    add('gpt-3.5', ['openai-gpt35']);
  }
  if (PROVIDER_MAP.has('anthropic-claude')) {
    add('claude', ['anthropic-claude']);
  }
  if (PROVIDER_MAP.has('ollama-gpt-oss-120b')) {
    add('gpt-oss', ['ollama-gpt-oss-120b']);
  }
  if (PROVIDER_MAP.has('gemini-pro')) {
    add('gemini-pro', ['gemini-pro']);
  }

  return Object.fromEntries(
    Object.entries(lookup).map(([key, set]) => [key, Array.from(set)])
  );
}

function createInitialState() {
  return {
    categories: new Set(),
    variants: new Set(),
    providers: new Set(),
    tasks: new Set(),
    languages: new Set(),        // NEW: separate language tracking
    promptLevels: new Set(),     // NEW: separate prompt level tracking
    frameworks: new Set(),        // NEW: framework tracking
    codeStyles: new Set(),        // NEW: code style tracking
    presetSelections: [],
    appliedPresetKeys: new Set(),
    preferredProviders: [],
    legacyPresets: [],
    unknownPresets: [],
    unknownCategories: [],
    unknownVariants: [],
    unknownProviders: [],
    autoPreset: true,
    includeBrowser: false,
    explicitIncludeBrowser: false,
    dryRun: false,  // Default to live mode
    runs: null,
    timeout: null,
    temperature: null,            // Single temperature value
    temperatures: [],             // Multiple temperature values
    help: false,
    listPresets: false,
    listProviders: false,
    listVariants: false,
    listCategories: false,
    listTasks: false,
    runAfterList: false
  };
}

function parseArgs(args, state) {
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    switch (arg) {
      case '-h':
      case '--help':
        state.help = true;
        break;
      case '--list-presets':
        state.listPresets = true;
        break;
      case '--list-providers':
        state.listProviders = true;
        break;
      case '--list-variants':
        state.listVariants = true;
        break;
      case '--list-categories':
        state.listCategories = true;
        break;
      case '--list-tasks':
        state.listTasks = true;
        break;
      case '--preset':
      case '--suite':
        i += 1;
        addPreset(args, i, arg, state);
        state.autoPreset = false;
        break;
      case '--basic':
      case '--compare':
        applyCliPreset('basic', state);
        state.autoPreset = false;
        break;
      case '--extended':
        applyCliPreset('extended', state);
        state.autoPreset = false;
        break;
      case '--ui':
      case '--browser':
        applyCliPreset('ui', state);
        state.autoPreset = false;
        break;
      case '--all':
      case '--full':
        applyCliPreset('full', state);
        state.autoPreset = false;
        break;
      case '--category':
      case '-c':
        i += 1;
        addCategoryArg(args, i, arg, state);
        state.autoPreset = false;
        break;
      case '--task':
      case '-t':
        i += 1;
        addTaskArg(args, i, arg, state);
        state.autoPreset = false;
        break;
      case '--provider':
      case '--providers':
      case '-p':
        i += 1;
        addProviderArg(args, i, arg, state);
        state.autoPreset = false;
        break;
      case '--variant':
      case '--variants':
      case '-v':
        i += 1;
        addVariantArg(args, i, arg, state);
        state.autoPreset = false;
        break;
      case '--js-only':
      case '--javascript':
        addVariant('js', state);
        state.autoPreset = false;
        break;
      case '--ts-only':
      case '--typescript':
        addVariant('ts', state);
        state.autoPreset = false;
        break;
      case '--language':
      case '--lang':
      case '-l':
        i += 1;
        addLanguageArg(args, i, arg, state);
        state.autoPreset = false;
        break;
      case '--prompt-level':
      case '--level':
        i += 1;
        addPromptLevelArg(args, i, arg, state);
        state.autoPreset = false;
        break;
      case '--all-prompt-levels':
        addAllPromptLevels(state);
        state.autoPreset = false;
        break;
      case '--temperature':
      case '--temp':
        i += 1;
        state.temperature = parseFloat(getArgValue(args, i, arg));
        if (isNaN(state.temperature) || state.temperature < 0 || state.temperature > 2) {
          throw new Error('--temperature must be a number between 0 and 2');
        }
        break;
      case '--temperatures':
      case '--temps':
        i += 1;
        addTemperaturesArg(args, i, arg, state);
        break;
      case '--temperature-range':
      case '--temp-range':
        i += 1;
        addTemperatureRangeArg(args, i, arg, state);
        break;
      case '--runs':
      case '-r':
        i += 1;
        state.runs = parsePositiveInteger(getArgValue(args, i, arg), '--runs');
        break;
      case '--timeout':
        i += 1;
        state.timeout = parsePositiveInteger(getArgValue(args, i, arg), '--timeout');
        break;
      case '--dry':
      case '--dry-run':
      case '--mock':
        state.dryRun = true;
        break;
      case '--include-browser':
        state.includeBrowser = true;
        state.explicitIncludeBrowser = true;
        break;
      case '--skip-browser':
        state.includeBrowser = false;
        state.explicitIncludeBrowser = true;
        break;
      default:
        if (arg.startsWith('-')) {
          throw new Error(`Unknown option: ${arg}`);
        }
        state.tasks.add(arg);
        state.autoPreset = false;
        break;
    }
  }
}

function addPreset(args, index, flag, state) {
  const value = getArgValue(args, index, flag);
  if (!applyCliPreset(value, state)) {
    if (PresetManager.getPreset(value)) {
      state.legacyPresets.push(value);
    } else {
      state.unknownPresets.push(value);
    }
  }
}

function addCategoryArg(args, index, flag, state) {
  const value = getArgValue(args, index, flag);
  addCategory(value, state);
}

function addTaskArg(args, index, flag, state) {
  const value = getArgValue(args, index, flag);
  state.tasks.add(value);
}

function addProviderArg(args, index, flag, state) {
  const value = getArgValue(args, index, flag);
  addProvider(value, state);
}

function addVariantArg(args, index, flag, state) {
  const value = getArgValue(args, index, flag);
  addVariant(value, state);
}

function getArgValue(args, index, flag) {
  if (index >= args.length) {
    throw new Error(`${flag} requires a value.`);
  }
  return args[index];
}

function parsePositiveInteger(value, flag) {
  const parsed = parseInt(value, 10);
  if (!Number.isFinite(parsed) || parsed < 1) {
    throw new Error(`${flag} must be a positive integer.`);
  }
  return parsed;
}

function applyCliPreset(name, state, { source = 'user' } = {}) {
  if (!name) return false;
  const normalizedInput = normalize(name);
  const mapped = PRESET_ALIASES[normalizedInput] || normalizedInput;
  const preset = CLI_PRESETS[mapped];
  if (!preset) {
    return false;
  }

  if (!state.appliedPresetKeys.has(mapped)) {
    state.appliedPresetKeys.add(mapped);
    state.presetSelections.push({ key: mapped, source });
  }

  if (Array.isArray(preset.categories)) {
    for (const category of preset.categories) {
      state.categories.add(category);
    }
  }
  if (Array.isArray(preset.variants)) {
    for (const variant of preset.variants) {
      state.variants.add(variant);
    }
  }
  if (Array.isArray(preset.providers)) {
    state.preferredProviders.push(...preset.providers);
  }
  if (preset.includeBrowser !== undefined && !state.explicitIncludeBrowser) {
    state.includeBrowser = preset.includeBrowser;
  }
  if (preset.runs && state.runs == null) {
    state.runs = preset.runs;
  }
  return true;
}

function addCategory(value, state) {
  if (!value) return;
  const normalized = normalize(value);
  const matches = CATEGORY_LOOKUP[normalized];
  if (matches && matches.length > 0) {
    matches.forEach(category => state.categories.add(category));
    return;
  }
  if (CATEGORY_DATA[value]) {
    state.categories.add(value);
    return;
  }
  const direct = Object.keys(CATEGORY_DATA).find(category => normalize(category) === normalized);
  if (direct) {
    state.categories.add(direct);
    return;
  }
  state.unknownCategories.push(value);
}

function addVariant(value, state) {
  if (!value) return;
  const normalized = normalize(value);
  const aliasTarget = VARIANT_ALIASES[normalized];
  const key = aliasTarget || normalized;
  const group = VARIANT_GROUPS[key];
  if (group && group.length > 0) {
    group.forEach(variant => state.variants.add(variant));
    return;
  }
  if (ALL_VARIANTS.includes(value)) {
    state.variants.add(value);
    return;
  }
  const direct = ALL_VARIANTS.find(variant => normalize(variant) === normalized);
  if (direct) {
    state.variants.add(direct);
    return;
  }
  state.unknownVariants.push(value);
}

function addProvider(value, state) {
  if (!value) return;
  const normalized = normalize(value);
  const matches = PROVIDER_LOOKUP[normalized];
  if (matches && matches.length > 0) {
    matches.forEach(name => state.providers.add(name));
    return;
  }
  if (PROVIDER_MAP.has(value)) {
    state.providers.add(value);
    return;
  }
  const direct = PROVIDER_NAMES.find(name => normalize(name) === normalized);
  if (direct) {
    state.providers.add(direct);
    return;
  }
  state.unknownProviders.push(value);
}

function addLanguageArg(args, index, flag, state) {
  const value = getArgValue(args, index, flag);
  const languages = value.split(',').map(lang => lang.trim().toLowerCase());

  for (const lang of languages) {
    if (lang === 'javascript' || lang === 'js') {
      state.languages.add('javascript');
    } else if (lang === 'typescript' || lang === 'ts') {
      state.languages.add('typescript');
    } else if (lang === 'javascript-jsdoc' || lang === 'jsdoc') {
      state.languages.add('javascript-jsdoc');
    } else if (lang === 'all') {
      state.languages.add('javascript');
      state.languages.add('typescript');
      state.languages.add('javascript-jsdoc');
      break;
    } else {
      throw new Error(`Unknown language: ${lang}. Use: js, ts, jsdoc, or all`);
    }
  }
}

function addPromptLevelArg(args, index, flag, state) {
  const value = getArgValue(args, index, flag);
  const levels = value.split(',').map(level => level.trim().toLowerCase());

  const validLevels = ['novice', 'beginner', 'intermediate', 'advanced', 'expert'];

  for (const level of levels) {
    if (validLevels.includes(level)) {
      state.promptLevels.add(level);
    } else if (level === 'all') {
      validLevels.forEach(l => state.promptLevels.add(l));
      break;
    } else {
      throw new Error(`Unknown prompt level: ${level}. Use: novice, beginner, intermediate, advanced, expert, or all`);
    }
  }
}

function addAllPromptLevels(state) {
  const levels = ['novice', 'beginner', 'intermediate', 'advanced', 'expert'];
  levels.forEach(level => state.promptLevels.add(level));
}

function addTemperaturesArg(args, index, flag, state) {
  const value = getArgValue(args, index, flag);
  const temps = value.split(',').map(t => t.trim());

  for (const temp of temps) {
    const parsed = parseFloat(temp);
    if (isNaN(parsed) || parsed < 0 || parsed > 2) {
      throw new Error(`--temperatures values must be numbers between 0 and 2 (got: ${temp})`);
    }
    state.temperatures.push(parsed);
  }
}

function addTemperatureRangeArg(args, index, flag, state) {
  const value = getArgValue(args, index, flag);
  const parts = value.split(',').map(p => p.trim());

  if (parts.length !== 3) {
    throw new Error(`--temperature-range requires start,end,step format (e.g., 0.0,1.5,0.5)`);
  }

  const [start, end, step] = parts.map(parseFloat);

  if (isNaN(start) || isNaN(end) || isNaN(step)) {
    throw new Error(`--temperature-range values must be numbers (got: ${value})`);
  }

  if (start < 0 || start > 2 || end < 0 || end > 2) {
    throw new Error(`--temperature-range start and end must be between 0 and 2`);
  }

  if (step <= 0) {
    throw new Error(`--temperature-range step must be > 0`);
  }

  if (start > end) {
    throw new Error(`--temperature-range start must be <= end`);
  }

  // Generate temperature values
  for (let temp = start; temp <= end; temp += step) {
    state.temperatures.push(Math.round(temp * 100) / 100); // Round to 2 decimal places
  }
}

function finalizePlan(state) {
  if (state.autoPreset) {
    applyCliPreset('basic', state, { source: 'auto' });
  }

  if (state.categories.size === 0) {
    state.categories.add('1-foundations');
  }

  // Generate variant combinations from languages and prompt levels
  let finalVariants = Array.from(state.variants);

  // If user specified languages or prompt levels, generate combinations
  if (state.languages.size > 0 || state.promptLevels.size > 0) {
    const languages = state.languages.size > 0
      ? Array.from(state.languages)
      : ['javascript', 'typescript']; // Default languages

    const promptLevels = state.promptLevels.size > 0
      ? Array.from(state.promptLevels)
      : ['expert']; // Default to expert level

    // Generate combinations using BenchmarkConfig helper
    const combinations = BenchmarkConfig.generateCombinations({
      languages,
      promptLevels,
      frameworks: Array.from(state.frameworks),
      codeStyles: Array.from(state.codeStyles)
    });

    // Add variant strings from combinations
    const generatedVariants = combinations.map(c => c.variantString);
    finalVariants = [...new Set([...finalVariants, ...generatedVariants])];
  }

  // If no variants at all, use defaults
  if (finalVariants.length === 0) {
    finalVariants = DEFAULT_VARIANT_PAIR;
  }

  const categories = Array.from(state.categories);
  if (!state.explicitIncludeBrowser) {
    state.includeBrowser = categories.some(category => BROWSER_CATEGORIES.has(category));
  }

  const providers = resolveProviders(state);
  const tasks = Array.from(state.tasks);

  if (providers.length === 0) {
    throw new Error('Provider is required. Use --provider to specify a model (e.g., --provider ollama-qwen3-30b).\nAvailable providers: ' + PROVIDER_NAMES.join(', '));
  }

  const warnings = [];
  if (state.unknownPresets.length > 0) {
    warnings.push(`Unknown preset(s): ${state.unknownPresets.join(', ')}`);
  }
  if (state.unknownCategories.length > 0) {
    warnings.push(`Unknown category alias(es): ${state.unknownCategories.join(', ')}`);
  }
  if (state.unknownVariants.length > 0) {
    warnings.push(`Unknown variant alias(es): ${state.unknownVariants.join(', ')}`);
  }
  if (state.unknownProviders.length > 0) {
    warnings.push(`Unknown provider alias(es): ${state.unknownProviders.join(', ')}`);
  }

  return {
    categories,
    variants: finalVariants,
    providers,
    tasks,
    warnings,
    temperature: state.temperature, // Single temperature value
    temperatures: state.temperatures // Multiple temperature values
  };
}

function resolveProviders(state) {
  const ordered = [];
  const seen = new Set();

  const push = (name) => {
    if (!name || seen.has(name) || !PROVIDER_MAP.has(name)) return;
    seen.add(name);
    ordered.push(name);
  };

  // Only use explicitly specified providers
  Array.from(state.providers).forEach(push);

  // If no providers specified, use preferred providers from presets (if any)
  if (ordered.length === 0 && state.preferredProviders.length > 0) {
    state.preferredProviders.forEach(push);
  }

  return ordered;
}

function cloneConfig(base) {
  return {
    ...base,
    providers: base.providers.map(provider => ({ ...provider })),
    variants: [...base.variants],
    categories: Object.fromEntries(
      Object.entries(base.categories).map(([key, value]) => [key, { ...value }])
    ),
    evaluation: Object.fromEntries(
      Object.entries(base.evaluation).map(([key, value]) => [key, { ...value }])
    ),
    output: { ...base.output }
  };
}

function ensureProviderObjects(config) {
  config.providers = config.providers
    .map(entry => {
      if (typeof entry === 'string') {
        const fromMap = PROVIDER_MAP.get(entry);
        if (!fromMap) {
          console.warn(`⚠️  Unknown provider "${entry}" removed from configuration.`);
          return null;
        }
        return { ...fromMap };
      }
      if (entry && typeof entry === 'object') {
        return { ...entry };
      }
      return null;
    })
    .filter(Boolean);

  const seen = new Set();
  config.providers = config.providers.filter(provider => {
    if (seen.has(provider.name)) {
      return false;
    }
    seen.add(provider.name);
    return true;
  });

  if (config.providers.length === 0) {
    config.providers = BenchmarkConfig.providers.map(provider => ({ ...provider }));
  }
}

function listPresets() {
  console.log('\nCLI Presets (JS vs TS comparison):\n');
  for (const [key, preset] of Object.entries(CLI_PRESETS)) {
    console.log(`  ${key.padEnd(12)} ${preset.description}`);
  }

  console.log('\nLegacy DREAM presets:\n');
  const legacy = PresetManager.listPresets();
  for (const preset of legacy) {
    console.log(`  ${preset.key.padEnd(16)} ${preset.description}`);
  }
  console.log('');
}

function listVariants() {
  console.log('\nLanguage variants:\n');
  for (const [group, variants] of Object.entries(VARIANT_GROUPS)) {
    if (variants.length === 0) continue;
    console.log(`  ${group.padEnd(12)} ${variants.join(', ')}`);
  }
  console.log('');
}

function listCategories() {
  console.log('\nBenchmark categories:\n');
  for (const [key, data] of Object.entries(CATEGORY_DATA)) {
    const aliases = data.aliases.slice(0, 6).join(', ');
    console.log(`  ${key.padEnd(30)} ${data.description} (aliases: ${aliases || '—'})`);
  }

  console.log('\nCategory groups:\n');
  for (const [group, categories] of Object.entries(CATEGORY_GROUPS)) {
    if (group === 'all') continue;
    console.log(`  ${group.padEnd(12)} ${categories.join(', ')}`);
  }
  console.log('');
}

function listProviders() {
  console.log('\nProviders:\n');
  for (const provider of BenchmarkConfig.providers) {
    const kind = provider.baseUrl ? 'local' : 'cloud';
    const details = provider.description || provider.model || '';
    console.log(`  ${provider.name.padEnd(30)} [${kind}] ${details}`);
  }

  console.log('\nProvider groups:\n');
  for (const [group, names] of Object.entries(PROVIDER_LOOKUP)) {
    if (group === 'all' || names.length === 0) continue;
    if (names.length === 1 && names[0] === group) continue;
    if (group.length > 20) continue;
    console.log(`  ${group.padEnd(12)} ${names.join(', ')}`);
  }
  console.log('');
}

async function listTasks() {
  const runner = new BenchmarkRunner(cloneConfig(BenchmarkConfig));
  const tasks = await runner.loadTasks();
  const grouped = tasks.reduce((acc, task) => {
    if (!acc[task.category]) acc[task.category] = [];
    acc[task.category].push(task);
    return acc;
  }, {});

  console.log('\nAvailable tasks:\n');
  for (const [category, categoryTasks] of Object.entries(grouped)) {
    const meta = CATEGORY_DATA[category];
    console.log(`${meta ? meta.label : category}:`);
    categoryTasks
      .sort((a, b) => a.name.localeCompare(b.name))
      .forEach(task => {
        console.log(`  - ${task.name}: ${task.description}`);
      });
    console.log('');
  }
  console.log(`Total: ${tasks.length} tasks\n`);
}

function printHelp() {
  console.log(`
LLM TypeScript/JavaScript Benchmark Suite

Usage:
  node src/benchmarks/dream/index.js [options]

Quick start:
  node src/benchmarks/dream/index.js              # Basic JS vs TS comparison (default)
  node src/benchmarks/dream/index.js --extended   # Add scripting and backend tasks
  node src/benchmarks/dream/index.js --ui --include-browser

Key options:
  --basic | --extended | --ui | --all   Preset shortcuts
  -p, --provider <name>                Add provider or group (local, openai, gpt4, ...)
  -v, --variant <name>                 Add variant or group (js, ts, docs, react, ...)
  -c, --category <name>                Add category or group (foundations, backend, ui, ...)
  -t, --task <name>                    Focus on specific task (repeatable)
  --js-only | --ts-only               Restrict language family (legacy)

Dimension-based API (NEW):
  --language <lang>, -l <lang>        Languages to test (js, ts, jsdoc, all, or comma-separated)
  --prompt-level <level>              Prompt quality levels (novice, beginner, intermediate,
                                       advanced, expert, all, or comma-separated)
  --all-prompt-levels                 All 5 prompt levels (novice through expert)
  --temperature <n>, --temp <n>       LLM sampling temperature (0.0-2.0, default 1.0)
                                       Use 0.0 for deterministic, higher for variation
  --temperatures <list>, --temps <list>
                                       Test multiple temperatures (comma-separated, e.g., 0.0,0.5,1.0)
                                       Multiplies test runs by number of temperatures
  --temperature-range <start,end,step>
                                       Test temperature range (e.g., 0.0,1.5,0.5 tests 0.0, 0.5, 1.0, 1.5)

Other options:
  --runs <n>                          Override run count (default 1)
  --timeout <ms>                      Override per task timeout
  --include-browser | --skip-browser  Control browser-based tasks
  --dry, --dry-run, --mock            Use mock LLM responses (default: live mode)
  --list-presets | --list-providers | --list-variants | --list-categories | --list-tasks
  -h, --help                          Show this help message

Examples:
  # Test JS vs TS, all prompt levels, 5 runs each
  node src/benchmarks/dream/index.js --category foundations --language js,ts --all-prompt-levels --provider ollama-qwen3-30b --runs 5

  # Test prompt effectiveness: novice vs expert
  node src/benchmarks/dream/index.js --category foundations --language js --prompt-level novice,expert --provider ollama-gpt-oss-20b --runs 3

  # High temperature for code variation analysis
  node src/benchmarks/dream/index.js --category foundations --language ts --temperature 1.0 --provider ollama-qwen3-30b --runs 5

  # Deterministic testing (zero temperature)
  node src/benchmarks/dream/index.js --category foundations --language js --temperature 0.0 --provider ollama-gpt-oss-120b

  # Test multiple temperatures (multiplies test runs)
  node src/benchmarks/dream/index.js --task fibonacci --language js --temperatures 0.0,0.5,1.0,1.5 --provider ollama-qwen3-30b --runs 3

  # Temperature range testing
  node src/benchmarks/dream/index.js --task expression-evaluator --language js,ts --temperature-range 0.0,2.0,0.5 --provider ollama-gpt-oss-20b

  # Use mock responses for testing (dry mode)
  node src/benchmarks/dream/index.js --task fibonacci --language js,ts --dry

  # Legacy variant-based API still works
  node src/benchmarks/dream/index.js --task fibonacci --variant javascript-expert,typescript-expert --provider ollama-qwen3-30b
`);
}

function normalize(value) {
  return value?.toString().trim().toLowerCase() || '';
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(error => {
    console.error(error);
    process.exit(1);
  });
}

export { BenchmarkRunner, BenchmarkConfig };
