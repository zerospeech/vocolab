#!/usr/bin/env python3
import argparse
import os
# import pydoc
import sys
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

console = Console()
try:
    DOC_LOCATION = Path(os.environ.get('DOC_LOCATION'))
except TypeError:
    DOC_LOCATION = Path('/docs')


if not DOC_LOCATION.is_dir():
    console.print(f"Failed to load documentation DOC_LOCATION: {DOC_LOCATION} does not exist.")
    sys.exit(1)

DOCUMENTS = [x.stem for x in DOC_LOCATION.glob("*.md") if not x.stem.startswith('_')]


def view_document(name: str):
    document = DOC_LOCATION / f"{name}.md"
    with document.open() as fp:
        data = "".join(fp.readlines())

    with console.pager():
        console.print(Markdown(data))


def list_documents():
    table = Table(title="List of Items")
    table.add_column("Index")

    for file in DOCUMENTS:
        table.add_row(file)

    console.print(table)
    sys.exit(1)


def cmd(argv=None):
    argv = argv if argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description="documentation viewer")

    # arguments
    subparsers = parser.add_subparsers(dest='command')

    # list documents
    document_list = subparsers.add_parser('list', help="List Documents")

    view = subparsers.add_parser('view', help="View a Document")
    view.add_argument("name", type=str)

    return parser.parse_args(argv), parser


if __name__ == '__main__':
    args, p = cmd()

    if args.command == "list":
        list_documents()
    elif args.command == "view":
        view_document(args.name)
    else:
        p.print_help()


