#!/usr/bin/env python3
"""Export control episodes from frozen telemetry-v2 artifacts, without OCR."""
import argparse

from acc_telemetry.application.control_episodes import write_control_episodes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('session')
    parser.add_argument('output')
    parser.add_argument('--annotations')
    parser.add_argument('--settings')
    args = parser.parse_args()
    print(write_control_episodes(args.session, args.output,
                                 annotations_path=args.annotations, settings_path=args.settings))


if __name__ == '__main__':
    main()
