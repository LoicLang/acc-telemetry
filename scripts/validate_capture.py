#!/usr/bin/env python3
"""Validate existing telemetry-v2 evidence without OCR or media extraction."""
import argparse
import json
from pathlib import Path

from acc_telemetry.application.capture_validation import evaluate_session
from acc_telemetry.application.session_artifacts import check_destination
from acc_telemetry.application.validation_config import load_validation_settings


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts',type=Path,required=True)
    parser.add_argument('--annotations',type=Path,required=True)
    parser.add_argument('--capture',type=Path,help='defaults to capture.json alongside labels')
    parser.add_argument('--validation-config',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv)
    target=check_destination(args.output,args.annotations)
    report=evaluate_session(args.artifacts,args.annotations,args.capture or args.annotations.with_name('capture.json'),
                            settings=load_validation_settings(args.validation_config))
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('x') as handle:
        json.dump(report,handle,indent=2,allow_nan=False); handle.write('\n')
    print(target)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
