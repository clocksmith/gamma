"""Fully stored source alternatives for three already exposed graph problems.

This module reads public predecessor source and returns text. It never executes
candidate source or opens the private corpus. Helpers are repeated in every
standalone successor; a flat-literal encoder must pay for all their bytes.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / "readable-v1" / "profiles"
METHODS = {"547": "findCircleNum", "841": "canVisitAllRooms", "1091": "shortestPathBinaryMatrix"}

PYTHON_HELPER = '''def breadth_nodes(start_node, next_nodes):
    queue_values = [(start_node, 1)]
    queue_index = 0
    while queue_index < len(queue_values):
        node, depth = queue_values[queue_index]
        queue_index += 1
        yield node, depth
        for next_node in next_nodes(node):
            queue_values.append((next_node, depth + 1))

'''

JAVASCRIPT_HELPER = '''function* breadthNodes(startNode, nextNodes) {
  const queueValues = [[startNode, 1]];
  let queueIndex = 0;
  while (queueIndex < queueValues.length) {
    const [node, depth] = queueValues[queueIndex];
    queueIndex += 1;
    yield [node, depth];
    for (const nextNode of nextNodes(node)) {
      queueValues.push([nextNode, depth + 1]);
    }
  }
}
'''

PYTHON_BODIES = {
    "547": '''class Solution:
    def findCircleNum(self, isConnected):
        node_count = len(isConnected)
        visited_nodes = [False] * node_count
        def next_nodes(node):
            for next_node in range(node_count):
                if isConnected[node][next_node] and not visited_nodes[next_node]:
                    visited_nodes[next_node] = True
                    yield next_node
        component_count = 0
        for start_node in range(node_count):
            if not visited_nodes[start_node]:
                visited_nodes[start_node] = True
                component_count += 1
                for node, depth in breadth_nodes(start_node, next_nodes):
                    pass
        return component_count
''',
    "841": '''class Solution:
    def canVisitAllRooms(self, rooms):
        node_count = len(rooms)
        visited_nodes = [False] * node_count
        visited_nodes[0] = True
        def next_nodes(node):
            for next_node in rooms[node]:
                if not visited_nodes[next_node]:
                    visited_nodes[next_node] = True
                    yield next_node
        visited_count = 0
        for node, depth in breadth_nodes(0, next_nodes):
            visited_count += 1
        return visited_count == node_count
''',
    "1091": '''class Solution:
    def shortestPathBinaryMatrix(self, grid):
        if grid[0][0]:
            return -1
        grid_size = len(grid)
        grid[0][0] = 1
        def next_nodes(node):
            row, column = node
            for next_row in range(row - 1, row + 2):
                for next_column in range(column - 1, column + 2):
                    if 0 <= next_row < grid_size and 0 <= next_column < grid_size and grid[next_row][next_column] == 0:
                        grid[next_row][next_column] = 1
                        yield next_row, next_column
        for node, depth in breadth_nodes((0, 0), next_nodes):
            if node == (grid_size - 1, grid_size - 1):
                return depth
        return -1
''',
}

JAVASCRIPT_BODIES = {
    "547": '''class Solution {
  findCircleNum(isConnected) {
    const nodeCount = isConnected.length;
    const visitedNodes = new Array(nodeCount).fill(false);
    function* nextNodes(node) {
      for (let nextNode = 0; nextNode < nodeCount; nextNode += 1) {
        if (isConnected[node][nextNode] && !visitedNodes[nextNode]) {
          visitedNodes[nextNode] = true;
          yield nextNode;
        }
      }
    }
    let componentCount = 0;
    for (let startNode = 0; startNode < nodeCount; startNode += 1) {
      if (!visitedNodes[startNode]) {
        visitedNodes[startNode] = true;
        componentCount += 1;
        for (const pair of breadthNodes(startNode, nextNodes)) {
        }
      }
    }
    return componentCount;
  }
}
''',
    "841": '''class Solution {
  canVisitAllRooms(rooms) {
    const nodeCount = rooms.length;
    const visitedNodes = new Array(nodeCount).fill(false);
    visitedNodes[0] = true;
    function* nextNodes(node) {
      for (const nextNode of rooms[node]) {
        if (!visitedNodes[nextNode]) {
          visitedNodes[nextNode] = true;
          yield nextNode;
        }
      }
    }
    let visitedCount = 0;
    for (const pair of breadthNodes(0, nextNodes)) {
      visitedCount += 1;
    }
    return visitedCount === nodeCount;
  }
}
''',
    "1091": '''class Solution {
  shortestPathBinaryMatrix(grid) {
    if (grid[0][0]) {
      return -1;
    }
    const gridSize = grid.length;
    grid[0][0] = 1;
    function* nextNodes(node) {
      const [row, column] = node;
      for (let nextRow = row - 1; nextRow < row + 2; nextRow += 1) {
        for (let nextColumn = column - 1; nextColumn < column + 2; nextColumn += 1) {
          if (nextRow >= 0 && nextRow < gridSize && nextColumn >= 0 && nextColumn < gridSize && grid[nextRow][nextColumn] === 0) {
            grid[nextRow][nextColumn] = 1;
            yield [nextRow, nextColumn];
          }
        }
      }
    }
    for (const [node, depth] of breadthNodes([0, 0], nextNodes)) {
      if (node[0] === gridSize - 1 && node[1] === gridSize - 1) {
        return depth;
      }
    }
    return -1;
  }
}
''',
}


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_sources() -> dict[str, dict[str, dict[str, str]]]:
    result = {}
    for language, extension, helper, bodies in (
        ("python", "py", PYTHON_HELPER, PYTHON_BODIES),
        ("javascript", "js", JAVASCRIPT_HELPER, JAVASCRIPT_BODIES),
    ):
        result[language] = {}
        for problem_id in METHODS:
            original = (BASE / f"{language}-6-small-statements" / "assembled" / f"{problem_id}.{extension}").read_bytes().decode("utf-8")
            result[language][problem_id] = {"original": original, "shared-breadth": helper + bodies[problem_id]}
    return result


def provenance() -> list[dict]:
    rows = []
    for language, problems in build_sources().items():
        helper = PYTHON_HELPER if language == "python" else JAVASCRIPT_HELPER
        for problem_id, sources in problems.items():
            for variant, source in sources.items():
                rows.append({
                    "language": language, "problem_id": problem_id, "variant": variant,
                    "sha256": digest(source), "source_utf8_bytes": len(source.encode()),
                    "predecessor_sha256": digest(sources["original"]),
                    "helper_sha256": digest(helper) if variant == "shared-breadth" else None,
                    "helper_utf8_bytes": len(helper.encode()) if variant == "shared-breadth" else 0,
                    "entry_class": "Solution", "entry_method": METHODS[problem_id],
                    "qualification": "unknown_until_fresh_isolated_receipt",
                    "exposure": "previously_exposed_readable_v1_public_development",
                })
    return rows
