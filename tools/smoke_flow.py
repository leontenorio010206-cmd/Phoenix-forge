"""Source-mode wrapper for the acceptance routine shipped in the executable."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.acceptance import run

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='build/verification')
    parser.add_argument('--offscreen',action='store_true')
    args=parser.parse_args()
    raise SystemExit(run(args.output,args.offscreen))
