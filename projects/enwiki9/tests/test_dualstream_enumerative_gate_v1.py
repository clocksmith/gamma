import copy
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import dualstream_enumerative_gate_v1 as gate


class GateTests(unittest.TestCase):
    def test_actual_cost_required(self):
        costs = {n + "_rank_bytes": 1 for n in ("literal_definitions", "grammar_programs", "structure", "content", "arguments")}
        costs.update(count_table_bytes=5, stream_header_bytes=5, framing_bytes=10, exception_bytes=0)
        report = dict(costs=costs, complete_archive_bytes=25, raw_encoder_repeat_proved=False)
        self.assertEqual(gate.checked_cost(report, 25, True), costs)
        for change in (dict(complete_archive_bytes=26), dict(raw_encoder_repeat_proved=True),
                       dict(costs=dict(costs, complete_package=0))):
            with self.assertRaises(ValueError):
                gate.checked_cost(dict(report, **change), 25, True)

    def test_plan_requires_fixed_population_controls_and_limits(self):
        plan = dict(schema="gamma.enwiki9.enumerative-gate-plan.v1", candidate_id="test", arms=gate.ARMS,
                    stage="development", chunk_bytes=4096, population=dict(bytes=250000), frame_size=65536,
                    resources=dict(cpus=[2], memory_bytes=1073741824, scratch_bytes=67108864, swap_bytes=0, wall_seconds=600),
                    phase_cpu_seconds=60, phase_wall_seconds=90, phase_address_bytes=536870912,
                    runtime_files=["fixture"], kernel_basis="fixture")
        gate.validate_plan(plan, "test")
        for key, value in (("chunk_bytes", 8192), ("arms", gate.ARMS[:-1]), ("phase_cpu_seconds", 61), ("stage", "confirmation")):
            bad = copy.deepcopy(plan)
            bad[key] = value
            with self.assertRaises(ValueError):
                gate.validate_plan(bad, "test")


if __name__ == "__main__":
    unittest.main()
