"""Export a local full-lap perception package from existing telemetry-v2 artifacts."""
import argparse
import subprocess
from acc_telemetry.application.perception import write_perception


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--session',required=True)
    p.add_argument('--zones',required=True,help='source-bound coarse zone partition JSON')
    p.add_argument('--output',required=True,help='new package directory')
    p.add_argument('--lap',type=int,default=4)
    p.add_argument('--settings')
    p.add_argument('--detail-start',type=float,default=39.)
    p.add_argument('--detail-end',type=float,default=57.)
    p.add_argument('--sequence-start',type=float,default=49.)
    p.add_argument('--sequence-end',type=float,default=51.)
    p.add_argument('--sequence-step',type=float,default=.1)
    a=p.parse_args(argv)
    try:
        out=write_perception(a.session,a.zones,a.output,lap_number=a.lap,settings_path=a.settings,
            detail_start_s=a.detail_start,detail_end_s=a.detail_end,sequence_start_s=a.sequence_start,
            sequence_end_s=a.sequence_end,sequence_step_s=a.sequence_step)
    except (ValueError,OSError,KeyError,TypeError,subprocess.CalledProcessError) as exc:
        p.exit(2,f'Export impossible : {exc}\n')
    print(out/'index.html')
    return 0


if __name__=='__main__':raise SystemExit(main())
