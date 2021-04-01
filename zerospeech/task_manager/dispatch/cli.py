import argparse


def argument_parser(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', default=1, type=int, help="Number of worker processes. Defaults to single worker")

    # []
    parser.add_argument('--loop', type=float, help="")


def run_workers():
    pass
