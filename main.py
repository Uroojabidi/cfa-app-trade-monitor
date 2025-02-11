"""
A script to read trade data from CSV, apply compliance rules, and generate a report of suspicious trades.

This module includes functions for reading trade data, checking against compliance rules (front-running,
MNPI checks, restricted list, margin usage), and writing a report. Error handling is implemented to log
exceptions with stack traces to a rotating file (max 1MB per file, up to 5 backups).
"""

import csv
import os
import sys
import logging
import traceback
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from typing import List, Dict, Any


def read_trades(file_path: str) -> List[Dict[str, str]]:
    """
    Reads trade data from a CSV file and returns it as a list of dictionaries.

    Each trade is augmented with a 'TradeID' corresponding to its row index (1-based).

    Args:
        file_path (str): Path to the CSV file containing trades.

    Returns:
        List[Dict[str, str]]: List of dictionaries, each representing a trade with 'TradeID' added.

    Raises:
        FileNotFoundError: If `file_path` does not exist.
        PermissionError: If read permission is denied for `file_path`.
        UnicodeDecodeError: If file is not UTF-8 encoded.
        csv.Error: For CSV parsing errors.
        Exception: For unexpected errors (logged and re-raised).

    Side Effects:
        Reads from the filesystem.
    """
    trades: List[Dict[str, str]] = []
    try:
        with open(file_path, 'r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            for i, row in enumerate(reader, start=1):
                row["TradeID"] = str(i)
                trades.append(row)
    except (FileNotFoundError, PermissionError, UnicodeDecodeError, csv.Error) as e:
        logging.error(f"Error reading CSV file {file_path}: {str(e)}")
        logging.error(traceback.format_exc())
        raise
    except Exception as e:
        logging.error(f"Unexpected error reading CSV file {file_path}: {str(e)}")
        logging.error(traceback.format_exc())
        raise
    return trades


def check_rules(trades: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Applies compliance rules to trades to detect suspicious activity.

    Rules include:
    - Front-running: Employee trades preceding client trades in the same security.
    - MNPI (Material Non-Public Information): Large trades without public news.
    - Restricted List: Trades in restricted securities.
    - Margin Misuse: Margin usage in cash accounts.

    Args:
        trades (List[Dict[str, str]]): List of trades from `read_trades`.

    Returns:
        List[Dict[str, str]]: List of report entries for suspicious trades.

    Side Effects:
        Logs parsing errors to `compliance_errors.log`.
    """
    report: List[Dict[str, str]] = []

    employees = [t for t in trades if t.get("Trader_Type") == "Employee"]
    clients = [t for t in trades if t.get("Trader_Type") == "Client"]

    # RULE 1: Front-running
    for emp_trade in employees:
        emp_security = emp_trade.get("Security", "")
        emp_date_str = emp_trade.get("Date", "")
        emp_volume_str = emp_trade.get("Volume", "")

        try:
            emp_date = datetime.strptime(emp_date_str, '%Y-%m-%d')
            emp_volume = int(emp_volume_str)
        except (ValueError, TypeError) as e:
            logging.error(
                f"RULE 1: Error parsing date '{emp_date_str}' or volume '{emp_volume_str}' "
                f"for TradeID {emp_trade.get('TradeID', 'unknown')}: {e}"
            )
            logging.error(traceback.format_exc())
            continue

        next_day = emp_date + timedelta(days=1)

        for cli_trade in clients:
            if cli_trade.get("Security") != emp_security:
                continue

            cli_date_str = cli_trade.get("Date", "")
            cli_volume_str = cli_trade.get("Volume", "")

            try:
                cli_date = datetime.strptime(cli_date_str, '%Y-%m-%d')
                cli_volume = int(cli_volume_str)
            except (ValueError, TypeError) as e:
                logging.error(
                    f"RULE 1: Error parsing client date '{cli_date_str}' or volume '{cli_volume_str}' "
                    f"for TradeID {cli_trade.get('TradeID', 'unknown')}: {e}"
                )
                logging.error(traceback.format_exc())
                continue

            if emp_date <= cli_date <= next_day and emp_volume >= cli_volume:
                reason = (
                    f"Front-running: Employee volume ({emp_volume}) >= "
                    f"Client volume ({cli_volume}) on same or next day."
                )
                report.append({
                    "TradeID": emp_trade["TradeID"],
                    "Date": emp_date_str,
                    "Trader": emp_trade.get("Trader", ""),
                    "Security": emp_security,
                    "RuleID": "1",
                    "Reason": reason
                })

    # RULE 2: Potential MNPI - Large Volume
    for trade in trades:
        if trade.get("Trader_Type") != "Employee":
            continue

        volume_str = trade.get("Volume", "")
        avg_volume_str = trade.get("AvgVolume", "")
        public_news = trade.get("Public_News", "").lower()

        try:
            volume = int(volume_str)
            avg_volume = int(avg_volume_str)
        except (ValueError, TypeError) as e:
            logging.error(
                f"RULE 2: Error parsing volume '{volume_str}' or avg volume '{avg_volume_str}' "
                f"for TradeID {trade.get('TradeID', 'unknown')}: {e}"
            )
            logging.error(traceback.format_exc())
            continue

        if volume > 2 * avg_volume and public_news == "no":
            reason = (
                f"Potential MNPI: trade volume ({volume}) > 2× avg volume ({avg_volume}) "
                "with no public news."
            )
            report.append({
                "TradeID": trade["TradeID"],
                "Date": trade.get("Date", ""),
                "Trader": trade.get("Trader", ""),
                "Security": trade.get("Security", ""),
                "RuleID": "2",
                "Reason": reason
            })

    # RULE 20: Restricted List Check
    for trade in trades:
        if trade.get("Trader_Type") != "Employee":
            continue

        security = trade.get("Security", "")
        restricted_list = trade.get("Restricted_List", "")

        if restricted_list and security == restricted_list:
            reason = f"Employee Code Violation: Security ({security}) is on the restricted list."
            report.append({
                "TradeID": trade["TradeID"],
                "Date": trade.get("Date", ""),
                "Trader": trade.get("Trader", ""),
                "Security": security,
                "RuleID": "20",
                "Reason": reason
            })

    # RULE 25: Margin Used in a Cash Account
    for trade in trades:
        if trade.get("Trader_Type") != "Employee":
            continue

        margin_used = trade.get("MarginUsed", "").lower()
        client_agreement = trade.get("ClientAgreement", "").lower()

        if margin_used == "yes" and client_agreement == "cashaccount":
            reason = "Margin Use Not Authorized: 'MarginUsed=Yes' in a 'CashAccount'."
            report.append({
                "TradeID": trade["TradeID"],
                "Date": trade.get("Date", ""),
                "Trader": trade.get("Trader", ""),
                "Security": trade.get("Security", ""),
                "RuleID": "25",
                "Reason": reason
            })

    return report


def write_report(report: List[Dict[str, str]], output_file: str) -> None:
    """
    Writes the suspicious trades report to a CSV file.
    Ensures the output directory exists, preventing failures.

    Args:
        report (List[Dict[str, str]]): Suspicious trades to report.
        output_file (str): Path to the output CSV file.

    Side Effects:
        - Creates missing directories automatically.
        - Writes data to the CSV file.
        - Logs errors but does NOT fail the program execution.
    """
    fieldnames = ["TradeID", "Date", "Trader", "Security", "RuleID", "Reason"]

    try:
        # Ensure the directory exists, create it if missing
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # Open and write to the CSV file
        with open(output_file, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for entry in report:
                writer.writerow(entry)

        logging.info(f"Report successfully written to {output_file}")
        print(f"✅ Report successfully written to: {output_file}")

    except (PermissionError, IsADirectoryError, csv.Error) as e:
        logging.error(f"⚠️ Error writing report to {output_file}: {str(e)}")
        logging.error(traceback.format_exc())
        print(f"⚠️ Warning: Could not write report to {output_file}. Check permissions.")

    except Exception as e:
        logging.error(f"⚠️ Unexpected error writing report to {output_file}: {str(e)}")
        logging.error(traceback.format_exc())
        print(f"⚠️ Warning: Unexpected issue while writing the report. Continuing execution.")



def main() -> None:
    """
    Orchestrates the compliance check workflow.

    Logs are saved to `compliance_errors.log` with rotation (1MB per file, 5 backups).

    Raises:
        SystemExit: Exits with code 1 on critical errors.
    """
    try:
        logging.basicConfig(
            handlers=[
                RotatingFileHandler(
                    'compliance_errors.log',
                    maxBytes=1024 * 1024,  # 1MB
                    backupCount=5,
                    encoding='utf-8'
                )
            ],
            level=logging.ERROR,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        trades = read_trades("trades.csv")
        suspicious_report = check_rules(trades)

        output_file = (
            "/app/suspicious_trades_report.csv"
            if os.getenv("RUNNING_IN_DOCKER")
            else "output/suspicious_trades_report.csv"
        )

        write_report(suspicious_report, output_file)
        print(f"Report generated: {output_file}")
    except Exception as e:
        logging.error(f"Critical error in main execution: {str(e)}")
        logging.error(traceback.format_exc())
        print("An error occurred. Check compliance_errors.log for details.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
