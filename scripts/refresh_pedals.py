#!/usr/bin/env python3
"""Refresh native automatic pedal channels without OCR or other extraction."""
import argparse
from acc_telemetry.application.pedal_refresh import refresh_pedals

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('session')
    parser.add_argument('output')
    args = parser.parse_args()
    print(refresh_pedals(args.session, args.output,
                         progress=lambda n, total: print(f'Pedals: {n}/{total}', flush=True)))
