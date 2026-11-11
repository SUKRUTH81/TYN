"""Generate an offline visual report from an existing run without calling any APIs."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from release_agent.visual_report import write_visual_report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', help='Run directory containing report.json and optional metrics.json')
    args = parser.parse_args()
    print(write_visual_report(args.directory))
