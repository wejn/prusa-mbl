#!/usr/bin/env python3
"""
run_gcode.py - Run a GCode sequence against a Prusa 3D printer,
               capture some output.

Usage:
    python run_gcode.py <device> <baud> [gcode_file]

    device     - Serial device path (e.g. /dev/ttyACM0)
    baud       - Baud rate (e.g. 115200)
    gcode_file - Optional file with GCode commands (one per line).
                 If omitted, a default sequence is used.

Default gcode is for mesh bed leveling.
You can, however, supply a file, and in it mark arbitrary gcodes
marked to be captured, by prefixing them with a star.

The capture will be written to gcode_<gcode>_<YYmmdd_HHMMSS>.txt.
"""

import argparse
from datetime import datetime
import os
from pathlib import Path
import re
import sys
import time

import serial

DEFAULT_SEQUENCE = [
    # Default sequence is a no-op. Supply a gcode file.
    "M117 Whatever dude...",
    "M105           ; ask current temp",
    "M114           ; ask current position",
    "*M300 S440 P80 ; beep",
]

SETTLE_WAIT            = 2.0     # seconds to wait after buffer reset
PRINTER_DETECT_TIMEOUT = 5.0     # seconds to wait for M115 response
COMMAND_TIMEOUT        = 5*60.0  # max seconds to wait for 'ok' per command
READLINE_TIMEOUT       = 0.1     # serial readline poll interval


class Color:
    """Minimalistic color wrapper."""

    # Foreground colors
    BLACK   = "\033[30m"
    RED     = "\033[31m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    BLUE    = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN    = "\033[36m"
    WHITE   = "\033[37m"

    # Background colors
    BG_BLACK   = "\033[40m"
    BG_RED     = "\033[41m"
    BG_GREEN   = "\033[42m"
    BG_YELLOW  = "\033[43m"
    BG_BLUE    = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN    = "\033[46m"
    BG_WHITE   = "\033[47m"

    # Styles
    BOLD      = "\033[1m"
    UNDERLINE = "\033[4m"
    RESET     = "\033[0m"

    @staticmethod
    def supports_color(file=sys.stdout):
        """Does the file (fd) support color? (tty + colorterm)."""
        term = os.environ.get("TERM", "")
        colorterm = os.environ.get("COLORTERM", "")
        return (
            file.isatty() and
            (colorterm in ("truecolor", "24bit") or "color" in term)
        )

    @staticmethod
    def colored(text, color="", bg_color="", style=""):
        """Return text with arbitrary coloring applied."""
        return f"{style}{color}{bg_color}{text}{Color.RESET}"

    @staticmethod
    def bold_fg(text, color=""):
        """Return text with bold foreground."""
        return Color.colored(text, color, style=Color.BOLD)

class Output:
    """Minimalistic colored output class."""
    STDOUT_SUPPORTS_COLOR = Color.supports_color(sys.stdout)
    STDERR_SUPPORTS_COLOR = Color.supports_color(sys.stderr)

    @staticmethod
    def info(text):
        """Print info text."""
        if Output.STDOUT_SUPPORTS_COLOR:
            print(Color.bold_fg(text, Color.GREEN))
        else:
            print(text)

    @staticmethod
    def error(text):
        """Print error text."""
        if Output.STDERR_SUPPORTS_COLOR:
            print(Color.bold_fg(text, Color.RED), file=sys.stderr)
        else:
            print(text)

    @staticmethod
    def beautify_incoming(text):
        """Beautify input from the printer."""
        pattern = r"<<\s*ok\s*(.*)"
        match = re.match(pattern, text)
        if match and Output.STDOUT_SUPPORTS_COLOR:
            rest, = match.groups()
            print(f"<< {Color.bold_fg("ok", Color.CYAN)} {rest}")
        else:
            print(text)

    @staticmethod
    def beautify_outgoing(text):
        """Beautify output to the printer."""
        pattern = r">>\s+(.*?)(|\s*;\s*(.*))$"
        m117_pattern = r">>\s+(M117)\s+(.*)"
        if Output.STDOUT_SUPPORTS_COLOR:
            match = re.match(pattern, text)
            m117_match = re.match(m117_pattern, text)
            if m117_match:
                command, comment = m117_match.groups()
                print(f">> {Color.bold_fg(command, Color.YELLOW)} "
                      f"{Color.bold_fg(comment, Color.MAGENTA)}")
            elif match:
                command, _, comment = match.groups()
                if comment:
                    print(f">> {Color.bold_fg(command, Color.YELLOW)} "
                          f"; {Color.bold_fg(comment, Color.MAGENTA)}")
                else:
                    print(f">> {Color.bold_fg(command, Color.YELLOW)}")
            else:
                print(text)
        else:
            print(text)


def open_serial(device: str, baud: int) -> serial.Serial:
    """
    Open serial *device* with given *baud* speed.
    """
    return serial.Serial(
        port=device,
        baudrate=baud,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=READLINE_TIMEOUT,
    )


def read_until_ok(ser: serial.Serial,
                  timeout: float,
                  capture: bool = False) -> tuple[bool, list[str]]:
    """
    Read lines from *ser* until an 'ok' line is received or *timeout* expires.
    Returns (ok_received, lines_read).
    """
    lines: list[str] = []
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        raw = ser.readline()
        if not raw:
            continue
        line = raw.decode("ascii", errors="replace").rstrip()
        if line:
            Output.beautify_incoming(f"<< {line}")
            if capture:
                lines.append(line)
        if line.lower().startswith("ok"):
            return True, lines

    return False, lines


def send_command(ser: serial.Serial,
                 cmd: str,
                 timeout: float = COMMAND_TIMEOUT,
                 capture: bool = False) -> tuple[bool, list[str]]:
    """
    Send command to the serial port, wait for 'ok', optionally catch output.
    Returns (ok_received, lines_read).
    """
    cmd = cmd.strip()
    if not cmd or cmd.startswith(";"):
        return True, []

    Output.beautify_outgoing(f">> {cmd}")
    ser.write((cmd + "\n").encode("ascii"))
    ser.flush()
    return read_until_ok(ser, timeout, capture=capture)


def verify_printer(ser: serial.Serial) -> bool:
    """
    Verify that the printer on *ser* device is alive an well by sending M115.
    """
    Output.info("** Verifying printer presence with M115 …")
    ser.reset_input_buffer()
    # the printer may need a moment after reset
    time.sleep(SETTLE_WAIT)
    ser.reset_input_buffer()

    ok, lines = send_command(ser, "M115", timeout=PRINTER_DETECT_TIMEOUT, capture=True)
    if not ok:
        return False

    # At least one line should contain FIRMWARE_NAME or similar
    combined = "\n".join(lines).upper()
    return ("FIRMWARE_NAME" in combined or "Prusa-Firmware" in combined) and ok


def load_sequence(path: str) -> list[str]:
    """
    Load gcode sequence from a file *path*.
    Returns list of the gcodes.
    """
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [l.strip() for l in lines if l.strip() and not l.strip().startswith(";")]


def save_output(lines: list[str], cmd: str) -> str:
    """
    Save gcode command *cmd* output *lines* to a timestamped file.
    Returns filename.
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_cmd = cmd.split(";")[0].rstrip().replace(" ", "_").lstrip("_")
    filename = f"gcode_{safe_cmd}_{ts}.txt"
    Path(filename).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return filename


def main() -> int:
    """
    The main source of pain.
    """
    parser = argparse.ArgumentParser(
        description="Run a GCode sequence on a Marlin printer, capturing G29 T output."
    )
    parser.add_argument("device", help="Serial device (e.g. /dev/ttyACM0)")
    parser.add_argument("baud",   type=int, help="Baud rate (e.g. 115200)")
    parser.add_argument("gcode_file", nargs="?", help="Optional GCode file (one command per line)")
    args = parser.parse_args()

    sequence = load_sequence(args.gcode_file) if args.gcode_file else DEFAULT_SEQUENCE

    try:
        ser = open_serial(args.device, args.baud)
    except serial.SerialException as exc:
        Output.error(f"!! Error opening {args.device}: {exc}")
        return 1

    with ser:
        if not verify_printer(ser):
            Output.error("!! Error: printer not detected (no valid M115 response).")
            return 1
        Output.info("** Printer detected.\n")

        for cmd in sequence:
            do_capture = False
            if cmd.startswith("*"):
                do_capture = True
                cmd = cmd[1:]
            ok, captured = send_command(ser, cmd, capture=do_capture)

            if not ok:
                Output.error(f"!! Error: timeout waiting for 'ok' after: {cmd}")
                return 1

            if do_capture:
                filename = save_output(captured, cmd)
                just_cmd = cmd.split(';')[0]
                Output.info(f"** output of [{just_cmd.strip()}] saved to: {filename}")

    Output.info("** Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
