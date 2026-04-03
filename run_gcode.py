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
from pathlib import Path
import sys
import time

import serial

DEFAULT_SEQUENCE = [
    # Default sequence is a no-op. Supply a gcode file.
    "M105          ; ask current temp",
    "M114          ; ask current position",
    "M300 S440 P80 ; beep",
]

SETTLE_WAIT            = 2.0     # seconds to wait after buffer reset
PRINTER_DETECT_TIMEOUT = 5.0     # seconds to wait for M115 response
COMMAND_TIMEOUT        = 5*60.0  # max seconds to wait for 'ok' per command
READLINE_TIMEOUT       = 0.1     # serial readline poll interval


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
            print(f"<< {line}")
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

    print(f">> {cmd}")
    ser.write((cmd + "\n").encode("ascii"))
    ser.flush()
    return read_until_ok(ser, timeout, capture=capture)


def verify_printer(ser: serial.Serial) -> bool:
    """
    Verify that the printer on *ser* device is alive an well by sending M115.
    """
    print("** Verifying printer presence with M115 …")
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
        print(f"!! Error opening {args.device}: {exc}", file=sys.stderr)
        return 1

    with ser:
        if not verify_printer(ser):
            print("!! Error: printer not detected (no valid M115 response).", file=sys.stderr)
            return 1
        print("** Printer detected.\n")

        for cmd in sequence:
            do_capture = False
            if cmd.startswith("*"):
                do_capture = True
                cmd = cmd[1:]
            ok, captured = send_command(ser, cmd, capture=do_capture)

            if not ok:
                print(f"!! Error: timeout waiting for 'ok' after: {cmd}", file=sys.stderr)
                return 1

            if do_capture:
                filename = save_output(captured, cmd)
                print(f"\n** {cmd} saved to: {filename}")

    print("\n** Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
