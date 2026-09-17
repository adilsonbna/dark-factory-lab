import json
import time
import sys
import argparse
from pathlib import Path

class EvalHarness:
    def __init__(self, catalog_path):
        with open(catalog_path, 'r') as f:
            self.catalog = json.load(f)
        self.results = []

    def inject_fault(self, scenario):
        print(f"[{scenario['id']}] Injecting fault: {scenario['fault_type']} on {scenario['target']}...")
        # TODO: HTTP POST to generator service
        # requests.post(f"http://generator:8080/inject", json=scenario)
        time.sleep(1) # Simulate network lag

    def wait_for_resolution(self, scenario_id):
        print(f"[{scenario_id}] Waiting for autonomous resolution...")
        # TODO: Poll orchestrator API for status: Resolved
        # We simulate the process for Milestone 2
        time.sleep(2)
        return {
            "status": "PASS",
            "detection_s": 15,
            "diagnosis_s": 45,
            "resolution_s": 300,
        }

    def run_scenario(self, scenario):
        start_time = time.time()
        self.inject_fault(scenario)
        verdict = self.wait_for_resolution(scenario['id'])
        
        result = {
            "scenario_id": scenario['id'],
            "verdict": verdict['status'],
            "timings": {
                "detection": verdict['detection_s'],
                "diagnosis": verdict['diagnosis_s'],
                "resolution": verdict['resolution_s']
            },
            "timestamp": time.time()
        }
        self.results.append(result)
        print(f"[{scenario['id']}] Result: {verdict['status']}\n")

    def run_all(self):
        print(f"Starting evaluation of {len(self.catalog['scenarios'])} scenarios...\n")
        for scenario in self.catalog['scenarios']:
            self.run_scenario(scenario)
        self.save_report()

    def save_report(self):
        report_path = Path("eval/results_latest.json")
        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"Evaluation complete. Report saved to {report_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="dark-factory-lab Evaluation Harness")
    parser.add_argument("--scenario", help="Run a specific scenario ID")
    args = parser.parse_args()

    harness = EvalHarness("eval/catalog.json")
    if args.scenario:
        scenario = next((s for s in harness.catalog['scenarios'] if s['id'] == args.scenario), None)
        if scenario:
            harness.run_scenario(scenario)
        else:
            print(f"Scenario {args.scenario} not found.")
            sys.exit(1)
    else:
        harness.run_all()
