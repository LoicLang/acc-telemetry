#!/usr/bin/env python3
"""Prepare independent review images or validate human-reviewed annotations."""
import argparse
import json
from pathlib import Path

from acc_telemetry.application.capture_annotations import prepare_annotations, validate_annotation_file
from acc_telemetry.application.validation_config import load_validation_settings
from acc_telemetry.application.annotation_reviews import consolidate_approvals


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    prepare=commands.add_parser('prepare')
    prepare.add_argument('--video',type=Path,required=True)
    prepare.add_argument('--profile',required=True)
    prepare.add_argument('--output',type=Path,required=True)
    prepare.add_argument('--selection',type=Path)
    prepare.add_argument('--role',choices=('development','holdout'),default='development')
    prepare.add_argument('--config',type=Path)
    prepare.add_argument('--probe-evidence',type=Path,help='reuse source-hashed FFprobe failure evidence; revalidate packets')
    validate=commands.add_parser('validate')
    validate.add_argument('--annotations',type=Path,required=True)
    consolidate=commands.add_parser('consolidate')
    consolidate.add_argument('--approval',type=Path,nargs='+',required=True)
    consolidate.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv)
    if args.command=='prepare':
        output=prepare_annotations(args.video,args.profile,args.output,
            settings=load_validation_settings(args.config),selection=args.selection,role=args.role,
            progress=lambda message:print(message,flush=True),probe_evidence=args.probe_evidence)
        print(output)
    elif args.command=='validate':
        print(json.dumps(validate_annotation_file(args.annotations),allow_nan=False,indent=2))
    else:
        print(consolidate_approvals(args.approval,args.output))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
