#!/usr/bin/env python3
"""
icloud_year_selector_cli.py

Command-line tool for downloading a user-specified range of years from iCloud Photos
using icloudpd. This avoids the long initial scan required to inventory the full library
by asking the user to manually enter the desired start and end years.

Features:
- **Multi-Account Management**: Saves and loads known Apple IDs from a local file.
- **Interactive Prompts**: Asks for Apple ID (select or new), destination path, dry run choice, and the desired year range.
- **Simplified Auth**: Offers to run `icloudpd --auth-only` for new IDs to generate cookies.
- **Native Dry Run**: Uses icloudpd's `--dry-run` flag for simulation.
- **Folder Structure**: Uses YYYY/MM-Mon format (e.g., 2024/06-Jun).
- Uses corrected exclusion date flags to ensure proper year range coverage for older icloudpd versions.
- Downloads files in **original** quality via `--size original`.

Usage:
  # Run the script and follow the prompts
  ./icloud_year_selector_tui.py
  
  # Run authentication only (only useful if prompted by the main script)
  ./icloud_year_selector_tui.py --auth-only

Notes:
- Requires Python 3.8+ and icloudpd on PATH (install with `python3 -m pip install --user icloudpd`).
- Known Apple IDs are stored in `known_apple_ids.txt` in the script's directory.

Author: Refactored by Gemini
"""

from __future__ import annotations
import argparse
import subprocess
import sys
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional

# --- Configuration Constants ---
DEFAULT_COOKIE_DIR = Path.home() / ".pyicloud"
DEFAULT_DEST = Path.home() / "iCloudPD_Test"
APPLE_ID_FILE = "known_apple_ids.txt"

# -----------------------------
# Utilities
# -----------------------------

def run_cmd_stream(cmd: List[str]):
    """Run command and stream stdout/stderr to the terminal (no capture)."""
    # Use Popen to allow streaming output directly to the console
    proc = subprocess.Popen(cmd)
    proc.wait()
    return proc.returncode

def load_apple_ids() -> List[str]:
    """Loads a list of unique Apple IDs from the storage file."""
    try:
        # Resolve path relative to the script's location
        script_dir = Path(sys.argv[0]).resolve().parent
        id_file_path = script_dir / APPLE_ID_FILE
        
        with open(id_file_path, 'r') as f:
            ids = [line.strip() for line in f if line.strip()]
        return sorted(list(set(ids)))
    except FileNotFoundError:
        return []

def save_apple_id(new_id: str, existing_ids: List[str]):
    """Saves a new Apple ID to the storage file if it doesn't already exist."""
    if new_id not in existing_ids:
        try:
            script_dir = Path(sys.argv[0]).resolve().parent
            id_file_path = script_dir / APPLE_ID_FILE
            
            with open(id_file_path, 'a') as f:
                f.write(new_id + '\n')
            print(f"Added '{new_id}' to the list of known Apple IDs.")
        except Exception as e:
            print(f"Warning: Could not save Apple ID to {APPLE_ID_FILE}: {e}")

def get_user_inputs() -> Tuple[str, Path, Path]:
    """Interactively prompts user for required inputs (Apple ID and destination)."""
    
    known_ids = load_apple_ids()
    
    # 1. Get username (Select or New)
    username = ""
    while not username:
        print("\n--- Apple ID Selection ---")
        if known_ids:
            print("Select a known Apple ID or enter a new one:")
            for i, uid in enumerate(known_ids):
                print(f"  [{i + 1}] {uid}")
            
            choice = input(f"Enter choice (1-{len(known_ids)}) or new email: ").strip()
            
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(known_ids):
                    username = known_ids[idx]
                else:
                    print("Invalid selection.")
            elif "@" in choice:
                username = choice
            else:
                print("Invalid input. Please enter a number or a valid email.")
        else:
            username = input(f"Enter your Apple ID email (e.g., bradblog@gmail.com): ").strip()
            if not username or "@" not in username:
                print("Invalid Apple ID format. Please try again.")
                username = ""

    # Check if this is a new ID
    is_new_id = username not in known_ids
    
    # Run auth-only if new ID is entered
    if is_new_id:
        auth_prompt = input(f"New Apple ID '{username}'. Run icloudpd --auth-only now? (Y/n): ").strip().lower()
        if auth_prompt in ('y', ''):
            cmd = ["icloudpd", "--auth-only", "--username", username, "--cookie-directory", str(DEFAULT_COOKIE_DIR)]
            print(f"\nRunning auth-only for user: {username}. Complete 2FA when prompted...")
            run_cmd_stream(cmd)
            # Save ID after successful auth attempt
            save_apple_id(username, known_ids)

    # 2. Hardcode cookie path
    cookie_dir = DEFAULT_COOKIE_DIR
    
    # 3. Get destination path
    dest_input = input(f"Enter destination directory (Default: {DEFAULT_DEST}): ").strip()
    
    # Use default if input is empty, otherwise resolve input path
    dest = Path(dest_input).expanduser().resolve() if dest_input else DEFAULT_DEST.resolve()
    
    print(f"\nUsing Apple ID: {username}")
    print(f"Using Cookie Dir: {cookie_dir}")
    print(f"Using Destination: {dest}\n")
    
    return username, cookie_dir, dest


def get_year_range() -> Tuple[int, int]:
    """Interactively prompts user for start and end year with validation."""
    this_year = datetime.now().year
    
    while True:
        try:
            # Get Start Year
            start_input = input(f"Enter START year (e.g., 2018): ").strip()
            if not start_input:
                print("Start year cannot be empty.")
                continue
            start_year = int(start_input)
            if not (1900 <= start_year <= this_year + 1):
                print(f"Start year must be between 1900 and {this_year + 1}.")
                continue

            # Get End Year (defaults to Start Year if empty)
            end_input = input(f"Enter END year (Default: {start_year}): ").strip()
            if not end_input:
                end_year = start_year 
            else:
                end_year = int(end_input)

            if not (1900 <= end_year <= this_year + 1):
                print(f"End year must be between 1900 and {this_year + 1}.")
                continue
            
            # Ensure start year is not after end year
            if start_year > end_year:
                print("Warning: Start year was after end year. Swapping range.")
                start_year, end_year = end_year, start_year
            
            return start_year, end_year
            
        except ValueError:
            print("Invalid input. Please enter a valid integer for the year.")


# -----------------------------
# Command builder and runner
# -----------------------------

def build_icloudpd_cmd(username: str, cookie_dir: Path, dest: Path,
                       start_year: int, end_year: int, extra_opts: List[str]) -> List[str]:
    """
    Builds the icloudpd command for the given year range using exclusion date filters.
    
    We use the exclusion flags (--skip-created-before and --skip-created-after) with
    corrected dates to achieve an inclusive range [START_YEAR, END_YEAR].
    """
    
    # To include everything from START_YEAR onward, we skip everything BEFORE its start (Jan 1 of the start year).
    skip_before_date = f"{start_year}-01-01"
    
    # To include everything up to END_YEAR, we skip everything AFTER the first day of the NEXT year (Jan 1 of END_YEAR + 1).
    skip_after_date = f"{end_year + 1}-01-01"
    
    cmd = [
        "icloudpd",
        "--username", username,
    ]
    cmd += [
        "--directory", str(dest),
        # Updated folder structure: YYYY/MM-Mon
        "--folder-structure", "{:%Y/%m-%b}",
        "--set-exif-datetime",
        "--size", "original", # Ensures highest quality download
        # Use exclusion flags with corrected date logic:
        "--skip-created-before", skip_before_date,  # Includes photos from START_YEAR onward
        "--skip-created-after", skip_after_date,    # Includes photos up to END_YEAR
    ]
    cmd += ["--cookie-directory", str(cookie_dir)]
    if extra_opts:
        cmd += extra_opts
    return cmd

# -----------------------------
# CSV logging
# -----------------------------

def write_csv_log(csv_path: Path, rows: List[List[str]]):
    """Appends command execution logs to a CSV file."""
    header = ["timestamp","range","command","dry_run"]
    exists = csv_path.exists()
    with csv_path.open("a", newline='') as fh:
        writer = csv.writer(fh)
        if not exists:
            writer.writerow(header)
        for r in rows:
            writer.writerow(r)

# -----------------------------
# Main
# -----------------------------

def main():
    ap = argparse.ArgumentParser(description="CLI tool to download a specific year range from iCloud Photos via icloudpd")
    ap.add_argument("--skip-videos", action="store_true", help="Add --skip-videos to icloudpd command")
    ap.add_argument("--auth-only", action="store_true", help="Run icloudpd --auth-only and exit")
    args = ap.parse_args()

    # NOTE: The --auth-only flag is handled within the get_user_inputs function now,
    # but the command line flag is retained for flexibility.
    if args.auth_only:
        username = input("Enter Apple ID for --auth-only authentication: ").strip()
        if not username:
            print("Apple ID cannot be empty. Exiting.")
            return

        cmd = ["icloudpd", "--auth-only"]
        cmd += ["--username", username]
        cmd += ["--cookie-directory", str(DEFAULT_COOKIE_DIR)]
        
        print(f"Running auth-only for user: {username}. Complete 2FA when prompted.")
        subprocess.run(cmd)
        return
    
    # Standard run flow: get all inputs
    username, cookie_dir, dest = get_user_inputs()
    
    # --- Dry Run Prompt (Default Y) ---
    dry_run_input = input("Perform a dry run (icloudpd --dry-run)? (Y/n): ").strip().lower()
    dry_run_mode = dry_run_input in ('y', '')
    print(f"Running in {'DRY RUN' if dry_run_mode else 'LIVE DOWNLOAD'} mode.")
    
    # Ensure destination directory exists before proceeding
    dest.mkdir(parents=True, exist_ok=True)
    
    # 1) Get year range from user
    print("\n--- Download Range Selection ---")
    start_year, end_year = get_year_range()
    
    # 2) Build command
    extra = []
    if args.skip_videos:
        extra.append("--skip-videos")
    
    # Add native icloudpd dry-run flag if enabled
    if dry_run_mode:
        extra.append("--dry-run")
        
    cmd = build_icloudpd_cmd(username, cookie_dir, dest, start_year, end_year, extra)
    
    # 3) Execute or display command
    # Formatting the command string for display, quoting paths with spaces
    cmd_str = ' '.join([f'"{c}"' if (' ' in c) else c for c in cmd])
    timestamp = datetime.now().isoformat()
    
    if dry_run_mode:
        print(f"\nStarting DRY RUN for years {start_year}-{end_year}. icloudpd will list files but not download them.")
    else:
        print(f"\nStarting LIVE DOWNLOAD for years {start_year}-{end_year}. This may take a long time...")

    print(f"Command: {cmd_str}")
    rc = run_cmd_stream(cmd)
    
    if rc != 0:
        print(f"\nicloudpd exited with code {rc}. Please check the output above for errors.")
    else:
        print(f"\nProcess completed successfully (icloudpd returned 0).")

    # 4) write CSV log
    csv_rows = [[timestamp, f"{start_year}-{end_year}", cmd_str, str(dry_run_mode)]]
    logdir = dest / "icloud_year_selector_logs"
    logdir.mkdir(exist_ok=True)
    csv_path = logdir / "run_history.csv" 
    write_csv_log(csv_path, csv_rows)
    print(f"Wrote run log to {csv_path}")
    print("Done.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting due to user interruption.")
        sys.exit(0)
