import argparse
import argcomplete
from ccAVD.cc import Cut, Cook


def interpreter():
    # Get cookiecutter output_directory from CLI argument or default
    parser = argparse.ArgumentParser(
        prog="Cook-and-cut",
        description="This script creates expanded data from cookiecutter templates.")
    parser.add_argument(
        '-in', '--input_directory', default='CSVs',
        help='Directory to keep the AVD repository produced by cookiecutter'
    )
    parser.add_argument(
        '-out', '--output_directory', default='.',
        help='Directory to keep the AVD repository produced by cookiecutter'
    )
    parser.add_argument(
        '-td', '--template_dir', default='.cc',
        help="Cookiecutter template directory"
    )
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    cc = Cut(args.input_directory)
    cc.cut(args.template_dir)
