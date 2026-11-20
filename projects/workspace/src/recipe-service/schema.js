// Relational SQLite / Cloudflare D1 schema for Fawn Managed Recipe Service.

export const RECIPE_SERVICE_SCHEMA_SQL = `
CREATE TABLE IF NOT EXISTS recipe_namespaces (
  namespace_id TEXT PRIMARY KEY,
  scope_kind TEXT NOT NULL CHECK (scope_kind IN ('workspace', 'catalog')),
  workspace_id TEXT NOT NULL,
  origin TEXT NOT NULL,
  template TEXT NOT NULL,
  read_scope TEXT,
  dag_key TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_recipe_namespaces_lookup
  ON recipe_namespaces (scope_kind, workspace_id, origin, template);

CREATE TABLE IF NOT EXISTS recipe_nodes (
  namespace_id TEXT NOT NULL,
  node_id TEXT NOT NULL,
  outline_hash TEXT NOT NULL,
  outline_slots_json TEXT NOT NULL,
  same_outline_clicks INTEGER NOT NULL DEFAULT 0,
  depth INTEGER NOT NULL DEFAULT 0,
  is_terminal INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (namespace_id, node_id)
);

CREATE TABLE IF NOT EXISTS recipe_edges (
  namespace_id TEXT NOT NULL,
  edge_key TEXT NOT NULL,
  from_node TEXT NOT NULL,
  to_node TEXT NOT NULL,
  before_outline TEXT NOT NULL,
  before_slots_json TEXT NOT NULL,
  before_clicks INTEGER NOT NULL DEFAULT 0,
  after_outline TEXT NOT NULL,
  after_slots_json TEXT NOT NULL,
  after_clicks INTEGER NOT NULL DEFAULT 0,
  step_kind TEXT NOT NULL CHECK (step_kind IN ('fill', 'select', 'click')),
  locator_json TEXT NOT NULL,
  slot_name TEXT,
  attempts INTEGER NOT NULL DEFAULT 1,
  completions INTEGER NOT NULL DEFAULT 1,
  total_cost_ms REAL NOT NULL DEFAULT 0,
  author_count INTEGER NOT NULL DEFAULT 1,
  promoted INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (namespace_id, edge_key)
);

CREATE INDEX IF NOT EXISTS idx_recipe_edges_ns
  ON recipe_edges (namespace_id, promoted);

CREATE TABLE IF NOT EXISTS recipe_edge_authors (
  namespace_id TEXT NOT NULL,
  edge_key TEXT NOT NULL,
  author_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY (namespace_id, edge_key, author_hash)
);

CREATE TABLE IF NOT EXISTS recipe_subrecipes (
  subrecipe_id TEXT PRIMARY KEY,
  scope_kind TEXT NOT NULL CHECK (scope_kind IN ('workspace', 'catalog')),
  workspace_id TEXT NOT NULL,
  origin TEXT NOT NULL,
  name TEXT NOT NULL,
  entry_outline TEXT NOT NULL,
  exit_outline TEXT NOT NULL,
  steps_json TEXT NOT NULL,
  revision INTEGER NOT NULL DEFAULT 1,
  updated_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_recipe_subrecipes_name
  ON recipe_subrecipes (scope_kind, workspace_id, origin, name);

-- Append-only trace intake for a future generation publisher. Each immutable row
-- is both the accepted input and the receipt (not a publication acknowledgment).
CREATE TABLE IF NOT EXISTS recipe_trace_acceptance (
  namespace_id TEXT NOT NULL,
  acceptance_seq INTEGER NOT NULL CHECK (acceptance_seq >= 1),
  submission_id TEXT NOT NULL,
  payload_digest TEXT NOT NULL CHECK (length(payload_digest) = 64),
  payload_json TEXT NOT NULL,
  accepted_at TEXT NOT NULL,
  PRIMARY KEY (namespace_id, acceptance_seq),
  UNIQUE (namespace_id, submission_id)
);

-- Immutable publication records. Latest generation is the scoped head.
CREATE TABLE IF NOT EXISTS recipe_graph_generations (
  namespace_id TEXT NOT NULL,
  generation INTEGER NOT NULL CHECK (generation >= 1),
  input_watermark INTEGER NOT NULL CHECK (input_watermark >= 1),
  compiler_version TEXT NOT NULL,
  snapshot_digest TEXT NOT NULL CHECK (length(snapshot_digest) = 64),
  generation_digest TEXT NOT NULL CHECK (length(generation_digest) = 64),
  snapshot_json TEXT NOT NULL,
  published_at TEXT NOT NULL,
  PRIMARY KEY (namespace_id, generation)
);

CREATE TABLE IF NOT EXISTS recipe_submissions (
  submission_id TEXT PRIMARY KEY,
  namespace_id TEXT NOT NULL,
  client_id TEXT NOT NULL,
  verification_id TEXT NOT NULL,
  response_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
`;
