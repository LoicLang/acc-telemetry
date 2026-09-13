"""Local CLI for the experimental, manually reviewed session dossier."""
import argparse

from acc_telemetry.application.session_report import write_report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session', required=True, help='telemetry-v2 artifact directory')
    parser.add_argument('--case', required=True, help='source-bound reviewed case JSON')
    parser.add_argument('--output', required=True, help='new Markdown file, outside raw/session')
    args = parser.parse_args(argv)
    try:
        output = write_report(args.session, args.case, args.output)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f'Export impossible : {exc}\n')
    print(output)


if __name__ == '__main__':
    main()
