import argparse
import os
import yaml
from sootty.exceptions import SoottyError
from .save import save_query, reload_query
from .storage import WireTrace
from .visualizer import Visualizer


def parse_args():
    parser = argparse.ArgumentParser(
        description="Converts .vcd wiretraces to .svg format."
    )
    parser.add_argument(
        "filename",
        nargs="?",
        default=None,
        metavar="FILENAME",
        type=str,
        help="input .vcd file (required unless -R flag is provided)",
    )
    parser.add_argument(
        "-s",
        "--start",
        type=str,
        metavar="FORMULA",
        dest="start",
        help='formula for the start of the window (ex: \
        "time 4", \
        "after time 2 & clk", \
        "x == y | z == const 15")',
    )
    parser.add_argument(
        "-e",
        "--end",
        type=str,
        metavar="FORMULA",
        dest="end",
        help="formula for the end of the window",
    )
    parser.add_argument(
        "-b",
        "--break",
        type=str,
        metavar="FORMULA",
        dest="breakpoints",
        help="formula for the points in time to be highlighted",
    )
    parser.add_argument(
        "-l", "--length", type=int, dest="length", help="number of cycles to display"
    )
    parser.add_argument(
        "-o",
        "--output",
        action="store_true",
        help="print to stdout (does not display on terminal)",
    )
    parser.add_argument(
        "-w",
        "--wires",
        type=str,
        metavar="LIST",
        dest="wires",
        help="comma-separated list of wires to view",
    )
    parser.add_argument(
        "-S",
        "--save",
        type=str,
        metavar="SAVENAME",
        help="Save current query for reuse in a .txt file",
    )
    parser.add_argument(
        "-R",
        "--reload",
        type=str,
        metavar="SAVENAME",
        help="Loads a saved query. Requires query name as string.",
    )
    args = parser.parse_args()

    if args.save is not None and args.reload is not None:
        raise SoottyError(
            f"Save and Reload flags should not be provided simultaneously."
        )
    if args.save is not None:
        save_query(args)  # Save args to file
    if args.reload is not None:
        args = reload_query(parser, args)  # Load unassigned args from file

    return (
        args.filename,
        args.wires,
        args.breakpoints,
        args.length,
        args.start,
        args.end,
        args.output,
    )


def main():
    filename, wires, breakpoints, length, start, end, output = parse_args()

    if filename is None:
        raise SoottyError("Input file is required. See --help for more info.")

    # Load vcd file into wiretrace object.
    wiretrace = WireTrace.from_vcd(filename)

    # Check that window bounds are well-defined.
    if end is not None and length is not None:
        raise SoottyError("Length and end flags should not be provided simultaneously.")

    # Calculate window bounds.
    if end is not None:
        if start is not None:
            start, end = wiretrace.compute_limits(start, end)
        else:
            start, end = wiretrace.compute_limits("time 0", end)
        length = end - start
    else:
        if start is not None:
            start, end = wiretrace.compute_limits(start, "time 0")
        else:
            start = 0
        length = length if length is not None else wiretrace.length() - start

    # Calculate breakpoints
    if breakpoints is not None:
        breakpoints = wiretrace.evaluate(breakpoints)

    if wires is not None:
        wires = set([name.strip() for name in wires.split(",")])

    # Convert wiretrace to graphical vector image.
    image = Visualizer().to_svg(
        wiretrace, start=start, length=length, wires=wires, breakpoints=breakpoints
    )

    if wires is not None and len(wires):
        raise Exception(
            f"Unknown wires {wires.__repr__()}\nThe following wires were detected in the wiretrace:\n{wiretrace.get_wire_names()}"
        )

    if not output:
        image.display()  # Show image in terminal (works in kitty, iterm)

    else:
        print(image.source)


if __name__ == "__main__":
    main()
