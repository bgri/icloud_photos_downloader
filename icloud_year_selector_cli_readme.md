
# iCloud Photo Downloader CLI (icloud_year_selector_cli.py)

This script provides an interactive command-line interface (CLI) wrapper for `icloudpd`, designed to simplify the process of selectively downloading photos and videos from specific year ranges in your iCloud library.

It completely bypasses the slow metadata scanning process by relying on manual year input and uses the robust date filtering available in `icloudpd`.

## ✨ Key Features

* **Multi-Account Management:** Stores and loads previously used Apple IDs from a simple text file (`known_apple_ids.txt`).

* **Targeted Downloading:** Prompts for a `START` year and `END` year to download the complete range between those two calendar years (inclusive).

* **Highest Quality:** Downloads all media at `original` resolution (`--size original`).

* **Custom Folder Structure:** Organizes media into clean `YYYY/MM-Mon` folders (e.g., `2024/06-Jun`).

* **Native Dry Run:** Uses the official `icloudpd --dry-run` flag to simulate the download, confirming file listings and authentication before any large transfers begin.

* **Guided Authentication:** Offers to run `icloudpd --auth-only` when a new Apple ID is entered.

## ⚙️ Prerequisites

1. **Python 3:** The script requires Python 3.8 or newer.

2. **icloudpd:** The `icloudpd` utility must be installed and accessible on your system's PATH.

   ```bash
   # Installation command for icloudpd (if not already installed)
   python3 -m pip install --user icloudpd


## 🚀 Usage

### 1\. Initial Setup

Ensure the script file (`icloud_year_selector_tui.py`) is executable:

```bash
chmod +x icloud_year_selector_tui.py
```

### 2\. Running the Tool

Execute the script directly from your terminal:

```bash
python3 ./icloud_year_selector_tui.py
```

### 3\. Interactive Prompts

The script will guide you through the following steps:

#### **A. Apple ID Selection**

  * If you have run the script before, it will list known Apple IDs. Enter the number corresponding to your ID, or enter a new email address.

  * **New IDs:** If you enter a new email, the script will prompt you to run `icloudpd --auth-only` to authenticate and save the cookie file. Say `Y` to proceed.

#### **B. Destination Directory**

  * Enter the path where you want the photos to be saved.

  * The default is `~/iCloudPD_Test`. Press **Enter** to use the default.

#### **C. Dry Run Confirmation**

  * **Perform a dry run (icloudpd --dry-run)? (Y/n):**

      * Press **Enter** (default) to run the simulation. `icloudpd` will list all files that would be downloaded but will not save them.

      * Enter `n` to proceed directly to the live download.

#### **D. Download Range Selection**

  * Enter the `START` year (e.g., `2005`).

  * Enter the `END` year (e.g., `2010`).

The script will then construct and execute the `icloudpd` command to download all photos created from **January 1st of the START year** through **December 31st of the END year**.

## 📁 File Structure

The script automatically creates and manages the following files and directories:

| **File/Directory** | **Location** | **Purpose** |
| :--- | :--- | :--- |
| `known_apple_ids.txt` | Script directory | Stores Apple IDs for quick selection on future runs. |
| `~/.pyicloud/` | Home directory | The standard location where `icloudpd` saves authentication cookies. |
| `[DESTINATION_PATH]/YYYY/MM-Mon/` | Destination folder | Where downloaded photos and videos are saved. (e.g., `/2024/06-Jun/`) |
| `[DESTINATION_PATH]/icloud_year_selector_logs/run_history.csv` | Destination folder | A log of all commands executed (or simulated), including the timestamp and year range. |

```
