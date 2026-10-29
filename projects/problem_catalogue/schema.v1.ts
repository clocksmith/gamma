// GENERATED from schema.py. Edit its declarative definitions, then regenerate.
// Partial fields are migration facts; these types do not assert runtime validation.
export type Json = null | boolean | number | string | ReadonlyArray<Json> | { readonly [key: string]: Json };
export type SourcePointer = {
  "repository": string;
  "revision": string | null;
  "path": string;
  "sha256": string;
  "selector": string | null;
};

export type Ref = {
  "kind": "problem" | "contract" | "approach" | "artifact" | "evidence" | "source" | "company" | "company-report" | "relationship" | "admission";
  "id": string;
  "version": number;
  "path": string;
  "sha256": string;
};

export type FileRef = {
  "path": string;
  "sha256": string;
  "bytes": number;
  "mediaType": string;
};

export type TextField = ({
  "status": "present";
  "value": string;
  "provenance": ReadonlyArray<SourcePointer>;
}) | ({
  "status": "missing";
  "reason": string;
}) | ({
  "status": "unknown";
  "reason": string;
}) | ({
  "status": "not-applicable";
  "reason": string;
});

export type ListField = ({
  "status": "present";
  "value": ReadonlyArray<Json>;
  "provenance": ReadonlyArray<SourcePointer>;
}) | ({
  "status": "missing";
  "reason": string;
}) | ({
  "status": "unknown";
  "reason": string;
}) | ({
  "status": "not-applicable";
  "reason": string;
});

export type JsonField = ({
  "status": "present";
  "value": Json;
  "provenance": ReadonlyArray<SourcePointer>;
}) | ({
  "status": "missing";
  "reason": string;
}) | ({
  "status": "unknown";
  "reason": string;
}) | ({
  "status": "not-applicable";
  "reason": string;
});

export type Interface = {
  "language": string;
  "kind": "function" | "class" | "sql" | "unknown";
  "declaration": ({
    "status": "present";
    "value": Json;
    "provenance": ReadonlyArray<SourcePointer>;
  }) | ({
    "status": "missing";
    "reason": string;
  }) | ({
    "status": "unknown";
    "reason": string;
  }) | ({
    "status": "not-applicable";
    "reason": string;
  });
  "nativeMetadata": JsonField;
};

export type Stage = {
  "id": string;
  "type": "reasoning" | "coding" | "design" | "validation" | "simulation";
  "title": TextField;
  "question": TextField;
  "explanation": TextField;
  "rationale": TextField;
  "instructions": ListField;
  "observations": ListField;
  "hints": ListField;
  "requirementIds": ListField;
  "checks": ReadonlyArray<Ref>;
  "artifacts": ReadonlyArray<Ref>;
  "native": Ref;
};

export type Problem = {
  "kind": "problem";
  "id": string;
  "version": number;
  "schema": "study.record.v1";
  "origin": ReadonlyArray<SourcePointer>;
  "title": TextField;
  "type": "coding" | "system-design" | "sql" | "ml-design" | "ood" | "unknown";
  "topics": ListField;
  "difficulty": JsonField;
  "aliases": ReadonlyArray<Json>;
  "contracts": ReadonlyArray<Ref>;
  "approaches": ReadonlyArray<Ref>;
  "artifacts": ReadonlyArray<Ref>;
  "evidence": ReadonlyArray<Ref>;
  "sources": ReadonlyArray<Ref>;
  "companyReports": ReadonlyArray<Ref>;
  "relationships": ReadonlyArray<Ref>;
  "identity": {
    "status": "source-declared" | "reviewed" | "unresolved";
    "explanation": string;
  };
};

export type Contract = {
  "kind": "contract";
  "id": string;
  "version": number;
  "schema": "study.record.v1";
  "origin": ReadonlyArray<SourcePointer>;
  "problemId": string;
  "variantId": string;
  "variantLabel": TextField;
  "statement": TextField;
  "contentScope": "full-statement" | "preview" | "authored" | "unknown";
  "requirements": ListField;
  "constraints": ListField;
  "assumptions": ListField;
  "clarifyingQuestions": ListField;
  "examples": ListField;
  "interfaces": ReadonlyArray<Interface>;
  "effects": JsonField;
  "comparison": JsonField;
  "sources": ReadonlyArray<Ref>;
  "native": ReadonlyArray<Ref>;
};

export type Approach = {
  "kind": "approach";
  "id": string;
  "version": number;
  "schema": "study.record.v1";
  "origin": ReadonlyArray<SourcePointer>;
  "problemId": string;
  "contract": Ref;
  "title": TextField;
  "representation": "coding" | "conceptual-design" | "simulation" | "unknown";
  "explanation": TextField;
  "chooseWhen": ListField;
  "tradeoffs": ListField;
  "invariants": ListField;
  "hints": ListField;
  "stages": ReadonlyArray<Stage>;
  "sequenceStatus": "imported" | "draft" | "study-ready";
  "native": Ref;
};

export type Artifact = {
  "kind": "artifact";
  "id": string;
  "version": number;
  "schema": "study.record.v1";
  "origin": ReadonlyArray<SourcePointer>;
  "type": "implementation" | "diagram" | "graph-change" | "code-change" | "api-contract" | "workload" | "fault-schedule" | "test-suite" | "check" | "runtime" | "adapter" | "pseudocode" | "source-native" | "integration-reference";
  "title": string;
  "problemId": string | null;
  "approachId": string | null;
  "contract": (Ref) | (null);
  "file": ({
    "status": "present";
    "value": FileRef;
    "provenance": ReadonlyArray<SourcePointer>;
  }) | ({
    "status": "missing";
    "reason": string;
  }) | ({
    "status": "unknown";
    "reason": string;
  }) | ({
    "status": "not-applicable";
    "reason": string;
  });
  "externalLocator": JsonField;
  "language": string | null;
  "documentSchema": string | null;
  "executionKind": "conceptual" | "simulation" | "code" | "reference-only" | "unknown";
  "complexityClaims": ListField;
  "nativeMetadata": JsonField;
};

export type Evidence = {
  "kind": "evidence";
  "id": string;
  "version": number;
  "schema": "study.record.v1";
  "origin": ReadonlyArray<SourcePointer>;
  "contract": (Ref) | (null);
  "subjects": ReadonlyArray<Ref>;
  "method": "historical-report" | "execution" | "manual-review" | "simulation" | "measured-operation" | "model-generated-suggestion";
  "bindingStatus": "bound" | "partial" | "unbound";
  "bindings": JsonField;
  "results": JsonField;
  "report": Ref;
  "limitations": ReadonlyArray<string>;
  "admissionEffect": "none";
};

export type Source = {
  "kind": "source";
  "id": string;
  "version": number;
  "schema": "study.record.v1";
  "origin": ReadonlyArray<SourcePointer>;
  "title": string;
  "url": string | null;
  "publisher": TextField;
  "sourceType": string;
  "contentScope": "metadata" | "preview" | "full" | "reference-only";
  "license": TextField;
  "redistribution": "permitted" | "prohibited" | "unknown";
  "native": Ref;
};

export type Company = {
  "kind": "company";
  "id": string;
  "version": number;
  "schema": "study.record.v1";
  "origin": ReadonlyArray<SourcePointer>;
  "name": string;
  "aliases": ReadonlyArray<string>;
  "website": TextField;
};

export type CompanyReport = {
  "kind": "company-report";
  "id": string;
  "version": number;
  "schema": "study.record.v1";
  "origin": ReadonlyArray<SourcePointer>;
  "company": Ref;
  "contract": Ref;
  "source": Ref;
  "claim": "asked-in-interview" | "published-practice-question" | "company-inspired-practice" | "unresolved";
  "attribution": "company-published" | "candidate-reported" | "aggregator-reported" | "authored-practice" | "unverified";
  "frequency": JsonField;
  "reportedAt": TextField;
  "role": TextField;
  "nativeMetadata": JsonField;
};

export type Admission = {
  "kind": "admission";
  "id": string;
  "version": number;
  "schema": "study.record.v1";
  "origin": ReadonlyArray<SourcePointer>;
  "target": Ref;
  "contract": Ref;
  "purpose": "observer-reference" | "solver-reference" | "study-publication" | "simulation-execution" | "deployment-release";
  "decision": "approved" | "rejected" | "blocked" | "retired";
  "decidedBy": string;
  "decidedAt": string;
  "evidence": ReadonlyArray<Ref>;
  "explanation": string;
  "limitations": ReadonlyArray<string>;
};

export type Relationship = {
  "kind": "relationship";
  "id": string;
  "version": number;
  "schema": "study.record.v1";
  "origin": ReadonlyArray<SourcePointer>;
  "fromContract": Ref;
  "to": JsonField;
  "relation": "related" | "variant-of" | "source-cites" | "title-match-candidate" | "reviewed-contract-equivalent";
  "explanation": string;
  "sources": ReadonlyArray<Ref>;
  "evidence": ReadonlyArray<Ref>;
  "mergeAllowed": false;
};

export type EncoderIdentity = {
  "modelId": string;
  "modelRevision": string;
  "modelManifestSha256": string;
  "tokenizerManifestSha256": string;
  "adapterSha256": string;
  "runtimeManifestSha256": string;
  "pooling": string;
  "normalization": "none" | "l2";
  "dtype": string;
  "documentInstruction": string;
  "queryInstruction": string;
  "maxTokens": number;
  "truncation": string;
};

export type EmbeddingRecipe = {
  "chunker": "codepoint-window-v1";
  "maxCharacters": 1200;
  "overlapCharacters": 100;
};

export type EncoderContract = {
  "schema": "study.encoder-contract.v1";
  "command": ReadonlyArray<string>;
  "commandFile": string;
  "commandFileSha256": string;
  "encoderIdentity": EncoderIdentity;
  "recipe": EmbeddingRecipe;
  "dimensions": number;
};

export type EmbeddingEntry = {
  "id": string;
  "purpose": "problem-discovery" | "solution-study" | "artifact-search";
  "owner": Ref;
  "field": string;
  "chunkOrdinal": number;
  "textSha256": string;
  "vectorRow": number;
};

export type EmbeddingIndex = {
  "schema": "study.embedding-index.v1";
  "purpose": "problem-discovery" | "solution-study" | "artifact-search";
  "encoderFingerprint": string;
  "encoderProgramSha256": string;
  "encoderIdentity": EncoderIdentity;
  "recipe": EmbeddingRecipe;
  "dimensions": number;
  "encoding": "float32-le";
  "distance": "cosine" | "dot-product";
  "entries": ReadonlyArray<EmbeddingEntry>;
  "vectors": FileRef;
  "access": string;
};

export type EmbeddingRelease = {
  "schema": "study.embedding-release.v1";
  "indexes": ReadonlyArray<FileRef>;
};

export type GraphEndpoint = {
  "nodeId": string;
  "portId": string;
};

export type GraphPort = {
  "id": string;
  "direction": "in" | "out";
  "contractId": string;
};

export type GraphPosition = {
  "x": number;
  "y": number;
};

export type ArchitectureNode = {
  "id": string;
  "label": string;
  "componentId": string;
  "componentVersion": number;
  "parentId"?: string;
  "boundaryId"?: string;
  "lineageIds"?: ReadonlyArray<string>;
  "groupId"?: string | null;
};

export type ArchitectureEdge = {
  "id": string;
  "from": GraphEndpoint;
  "to": GraphEndpoint;
  "contractId": string;
  "mode": "request-response" | "event-stream" | "storage" | "local-call" | "message";
  "label"?: string;
};

export type ArchitectureGroup = {
  "id": string;
  "label": string;
  "kind": string;
  "capacity"?: number;
};

export type GraphContract = {
  "id": string;
  "version"?: number;
  "request"?: Json;
  "response"?: Json;
  [key: string]: Json | undefined;
};

export type GraphComponent = {
  "id": string;
  "version": number;
  "ports"?: ReadonlyArray<GraphPort>;
  [key: string]: Json | undefined;
};

export type GraphBoundary = {
  "id": string;
  "componentId": string;
  "componentVersion": number;
  "ports": ReadonlyArray<{
    "id": string;
    "direction": "in" | "out";
    "contractId": string;
    "target": GraphEndpoint;
  }>;
};

export type ArchitectureDefinitions = {
  "contracts": ReadonlyArray<GraphContract>;
  "components": ReadonlyArray<GraphComponent>;
  "boundaries": ReadonlyArray<GraphBoundary>;
};

export type ArchitectureGraph = {
  "nodes": ReadonlyArray<ArchitectureNode>;
  "edges": ReadonlyArray<ArchitectureEdge>;
  "groups": ReadonlyArray<ArchitectureGroup>;
};

export type ArchitectureModel = {
  "schema": "simulatte.architecture.v1";
  "id": string;
  "name": string;
  "description"?: string;
  "definitions": ArchitectureDefinitions;
  "graph": ArchitectureGraph;
  "simulation": {
    [key: string]: Json | undefined;
  } | null;
  "presentation": {
    "lucyd"?: {
      [key: string]: Json;
    };
    "study"?: {
      [key: string]: Json;
    };
  };
};

export type ArchitectureCommand = ({
  "op": "insert";
  "node": ArchitectureNode;
  "positions"?: {
    [key: string]: GraphPosition;
  };
}) | ({
  "op": "remove";
  "nodeId": string;
}) | ({
  "op": "connect";
  "edge": ArchitectureEdge;
}) | ({
  "op": "disconnect";
  "edgeId": string;
}) | ({
  "op": "reconnect";
  "edgeId": string;
  "edge": ArchitectureEdge;
  "reason": string;
}) | ({
  "op": "replace";
  "nodeId": string;
  "componentId": string;
  "componentVersion"?: number;
  "label"?: string;
  "migration": string;
}) | ({
  "op": "expand";
  "nodeId": string;
  "boundaryId": string;
  "nodes": ReadonlyArray<ArchitectureNode>;
  "edges": ReadonlyArray<ArchitectureEdge>;
  "positions"?: {
    [key: string]: {
      [key: string]: GraphPosition;
    };
  };
}) | ({
  "op": "rebind";
  "nodeId": string;
  "boundaryId": string;
  "reason": string;
}) | ({
  "op": "merge";
  "nodeIds": ReadonlyArray<string>;
  "node": ArchitectureNode;
  "reason": string;
  "positions"?: {
    [key: string]: GraphPosition;
  };
}) | ({
  "op": "relabel";
  "nodeId": string;
  "label": string;
}) | ({
  "op": "regroup";
  "nodeId": string;
  "groupId"?: string | null;
}) | ({
  "op": "setGroups";
  "groups": ReadonlyArray<ArchitectureGroup>;
}) | ({
  "op": "move";
  "nodeId": string;
  "view": "lucyd" | "study";
  "x": number;
  "y": number;
}) | ({
  "op": "bind";
  "nodeId": string;
  "binding": {
    [key: string]: Json;
  };
}) | ({
  "op": "unbind";
  "nodeId": string;
});

export type ArchitectureTransition = {
  "schema": "study.architectureTransition.v1";
  "before": ArchitectureModel;
  "operations": ReadonlyArray<ArchitectureCommand>;
  "after": ArchitectureModel;
};

export type SimulationNode = {
  "id": string;
  "classId": string;
  "label": string;
  "x": number;
  "y": number;
  "params": {
    [key: string]: Json;
  };
  "groupId"?: string | null;
  "overrides"?: {
    [key: string]: Json;
  };
};

export type SimulationEdge = {
  "id": string;
  "from": GraphEndpoint;
  "to": GraphEndpoint;
  "params": {
    [key: string]: Json;
  };
  "label"?: string;
};

export type SimulationGroup = {
  "id": string;
  "label": string;
  "kind": "zone" | "region" | "boundary" | "resource";
  "x": number;
  "y": number;
  "w": number;
  "h": number;
  "capacity"?: number;
  "collapsed"?: boolean;
};

export type SimulationNote = {
  "id": string;
  "text": string;
  "x": number;
  "y": number;
  "w"?: number;
};

export type SimulationFault = {
  "id": string;
  "atSec": number;
  "untilSec": number | null;
  "target": {
    "kind": "node" | "edge" | "group";
    "id": string;
  };
  "type": string;
  "params": {
    [key: string]: Json;
  };
};

export type SimulationClass = {
  "id": string;
  "label": string;
  "extends": string;
  "defaults": {
    [key: string]: Json;
  };
  "category"?: string;
  "glyph"?: string;
  "description"?: string;
};

export type SimulationSubsystem = {
  "id": string;
  "version": number;
  "label": string;
  "nodes": ReadonlyArray<SimulationNode>;
  "edges": ReadonlyArray<SimulationEdge>;
  "groups": ReadonlyArray<SimulationGroup>;
  "notes": ReadonlyArray<SimulationNote>;
  "faults": ReadonlyArray<SimulationFault>;
  "ports": ReadonlyArray<{
    "id": string;
    "label": string;
    "direction": "in" | "out";
    "target": GraphEndpoint;
  }>;
};

export type SimulationDiagramV4 = {
  "schema": "simulatte.systemDiagram.v4";
  "id": string;
  "name": string;
  "description"?: string;
  "seed": number;
  "run": {
    "horizonSec": number;
  };
  "classes": ReadonlyArray<SimulationClass>;
  "nodes": ReadonlyArray<SimulationNode>;
  "edges": ReadonlyArray<SimulationEdge>;
  "groups": ReadonlyArray<SimulationGroup>;
  "notes": ReadonlyArray<SimulationNote>;
  "faults": ReadonlyArray<SimulationFault>;
  "view": {
    "x": number;
    "y": number;
    "zoom": number;
  };
  "subsystems"?: ReadonlyArray<SimulationSubsystem>;
};

export type ConceptResponsibility = {
  "id": string;
  "label": string;
  "responsibility": string;
  "ports": ReadonlyArray<{
    "id": string;
    "direction": "in" | "out";
    "payloadType": string;
  }>;
  "binding"?: {
    "classId": string;
    "ports": {
      [key: string]: string;
    };
  };
};

export type SimulationDiagramV5 = {
  "schema": "simulatte.systemDiagram.v5";
  "id": string;
  "name": string;
  "description"?: string;
  "seed": number;
  "run": {
    "horizonSec": number;
  };
  "classes": ReadonlyArray<SimulationClass>;
  "nodes": ReadonlyArray<SimulationNode>;
  "edges": ReadonlyArray<SimulationEdge>;
  "groups": ReadonlyArray<SimulationGroup>;
  "notes": ReadonlyArray<SimulationNote>;
  "faults": ReadonlyArray<SimulationFault>;
  "view": {
    "x": number;
    "y": number;
    "zoom": number;
  };
  "subsystems"?: ReadonlyArray<SimulationSubsystem>;
  "intent"?: {
    "outcome": string;
    "users": string;
    "constraints": string;
    "success": string;
  };
  "concepts": ReadonlyArray<ConceptResponsibility>;
};

export type Study_edge = {
  "contractId": string;
  "from": {
    "nodeId": string;
    "portId": string;
  };
  "id": string;
  "label"?: string;
  "mode": "request-response" | "event-stream" | "storage" | "local-call";
  "to": {
    "nodeId": string;
    "portId": string;
  };
};

export type Study_graph = {
  "edges": ReadonlyArray<Study_edge>;
  "nodes": ReadonlyArray<Study_node>;
};

export type Study_node = {
  "definitionId": string;
  "id": string;
  "label": string;
  "lineageIds"?: ReadonlyArray<string>;
  "parentId"?: string;
  "position": {
    "x": number;
    "y": number;
  };
  "subsystemId"?: string;
  "version": number;
};

export type ComposableStudyDocument = {
  "components": ReadonlyArray<{
    "extends": {
      "id": string;
      "version": number;
    };
    "id": string;
    "label": string;
    "ports": ReadonlyArray<{
      "contractId": string;
      "direction": "in" | "out";
      "id": string;
    }>;
    "responsibility": string;
    "stateOwnership": ReadonlyArray<string>;
    "version": 1;
  }>;
  "contracts": ReadonlyArray<{
    "id": string;
    "request": {
      [key: string]: string;
    };
    "response": {
      [key: string]: string;
    };
    "version": 1;
  }>;
  "execution": {
    "implementation": null;
    "kind": "conceptual-design";
  };
  "problem": {
    "referenceId": string;
    "requirements": ReadonlyArray<{
      "id": string;
      "text": string;
    }>;
    "scope": string;
    "studyLabel": string;
  };
  "provenance": {
    "kind": "authored-practice";
    "note": string;
  };
  "references": ReadonlyArray<{
    "id": string;
    "scope": "background";
    "supports": string;
    "title": string;
    "url": string;
  }>;
  "schema": "simulatte.composableStudy.v2";
  "solutions": ReadonlyArray<{
    "acceptanceCases": ReadonlyArray<{
      "evidence"?: {
        "kind": "reference-test";
        "testFile": string;
        "testName": string;
      };
      "given": string;
      "id": string;
      "relatedRequirementIds": ReadonlyArray<string>;
      "then": string;
      "when": string;
    }>;
    "algorithms": ReadonlyArray<{
      "code": string;
      "guarantees": ReadonlyArray<string>;
      "id": string;
      "language": string;
      "ownerNodeId": string;
    }>;
    "apis": ReadonlyArray<{
      "errors": string;
      "method": string;
      "ownerNodeId": string;
      "path": string;
      "request": string;
      "response": string;
    }>;
    "assumptions": ReadonlyArray<string>;
    "chooseWhen": string;
    "id": string;
    "initialGraph": Study_graph;
    "stages": ReadonlyArray<{
      "checkIds": ReadonlyArray<string>;
      "code"?: ReadonlyArray<{
        "id": string;
        "kind": "api" | "pseudocode";
        "language": string;
        "text": string;
      }>;
      "explanation"?: string;
      "followupIds"?: ReadonlyArray<string>;
      "graph": Study_graph;
      "id": string;
      "invariants": ReadonlyArray<string>;
      "notes"?: ReadonlyArray<string>;
      "number": number;
      "operations": ReadonlyArray<({
        "node": Study_node;
        "op": "insert";
      }) | ({
        "edge": Study_edge;
        "op": "connect";
      }) | ({
        "edgeId": string;
        "op": "disconnect";
      }) | ({
        "edge": Study_edge;
        "edgeId": string;
        "op": "reconnect";
        "reason": string;
      }) | ({
        "nodeId": string;
        "op": "rebind";
        "reason": string;
        "subsystemId": string;
      }) | ({
        "definitionId": string;
        "label"?: string;
        "migration": string;
        "nodeId": string;
        "op": "replace";
      }) | ({
        "edges": ReadonlyArray<Study_edge>;
        "nodeId": string;
        "nodes": ReadonlyArray<Study_node>;
        "op": "expand";
        "subsystemId": string;
      }) | ({
        "node": Study_node;
        "nodeIds": ReadonlyArray<string>;
        "op": "merge";
        "reason": string;
      })>;
      "question": string;
      "reason": string;
      "title": string;
    }>;
    "title": string;
    "tradeoffs": ReadonlyArray<string>;
  }>;
  "subsystems": ReadonlyArray<{
    "definitionId": string;
    "id": string;
    "ports": ReadonlyArray<{
      "contractId": string;
      "direction": "in" | "out";
      "id": string;
      "target": {
        "nodeId": string;
        "portId": string;
      };
    }>;
    "version": 1;
  }>;
  "version": 1;
};

export type StudyRecord = Problem | Contract | Approach | Artifact | Evidence | Source | Company | CompanyReport | Relationship | Admission;

export type LucydGraphDocument = ArchitectureModel | SimulationDiagramV4 | SimulationDiagramV5 | ComposableStudyDocument;
