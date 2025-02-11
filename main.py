"""
A simple script to read trade data from CSV,
apply basic compliance rules (e.g., front-running, MNPI checks),
and write any suspicious trades to an output report.
"""

import csv
import os
from datetime import datetime, timedelta
from typing import List, Dict


def read_trades(file_path: str) -> List[Dict[str, str]]:
    """
    Reads trade data from a CSV file and returns it as a list of dictionaries.

    Each trade dictionary will be augmented with a 'TradeID' that reflects
    the row index (1-based).

    :param file_path: Path to the CSV file containing trades.
    :return: A list of dictionaries where each dictionary represents a trade.
    """
    trades = []
    with open(file_path, 'r', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        for i, row in enumerate(reader, start=1):
            # Add a trade identifier
            row["TradeID"] = str(i)
            trades.append(row)
    return trades


def check_rules(trades: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Applies a set of simplified compliance checks to the given trades
    (front-running, MNPI large volume, restricted list, margin usage).

    :param trades: A list of trade dictionaries (as returned by read_trades).
    :return: A list of report entries (dictionaries) describing suspicious trades.
    """
    report = []

    # Partition trades into employees vs. clients for front-running checks
    employees = [t for t in trades if t.get("Trader_Type") == "Employee"]
    clients = [t for t in trades if t.get("Trader_Type") == "Client"]

    # RULE 1: Front-running
    # -------------------------------------------------
    for emp_trade in employees:
        emp_security = emp_trade.get("Security", "")
        emp_date_str = emp_trade.get("Date", "")
        emp_volume_str = emp_trade.get("Volume", "")

        try:
            emp_date = datetime.strptime(emp_date_str, '%Y-%m-%d')
            emp_volume = int(emp_volume_str)
        except (ValueError, TypeError):
            # If we can't parse the date or volume, skip this trade
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
            except (ValueError, TypeError):
                continue

            # Check if client trades on same or next day AND employee volume >= client volume
            if emp_date <= cli_date <= next_day and emp_volume >= cli_volume:
                reason = (
                    f"Front-running: Employee volume ({emp_volume}) >= "
                    f"Client volume ({cli_volume}) on same or next day."
                )
                report.append({
                    "TradeID": emp_trade["TradeID"],
                    "Date": emp_trade["Date"],
                    "Trader": emp_trade.get("Trader", ""),
                    "Security": emp_security,
                    "RuleID": "1",
                    "Reason": reason
                })

    # RULE 2: Potential MNPI - Large Volume
    # -------------------------------------------------
    for trade in trades:
        if trade.get("Trader_Type") != "Employee":
            continue

        volume_str = trade.get("Volume", "")
        avg_volume_str = trade.get("AvgVolume", "")
        public_news = trade.get("Public_News", "").lower()

        try:
            volume = int(volume_str)
            avg_volume = int(avg_volume_str)
        except (ValueError, TypeError):
            continue

        # If volume > 2x average volume and there's no public news
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
    # -------------------------------------------------
    for trade in trades:
        if trade.get("Trader_Type") != "Employee":
            continue

        security = trade.get("Security", "")
        restricted_list = trade.get("Restricted_List", "")

        # If the trade's security is exactly the one in restricted_list
        if restricted_list and security == restricted_list:
            reason = (
                f"Employee Code Violation: Security ({security}) is on the restricted list."
            )
            report.append({
                "TradeID": trade["TradeID"],
                "Date": trade.get("Date", ""),
                "Trader": trade.get("Trader", ""),
                "Security": security,
                "RuleID": "20",
                "Reason": reason
            })

    # RULE 25: Margin Used in a Cash Account
    # -------------------------------------------------
    for trade in trades:
        if trade.get("Trader_Type") != "Employee":
            continue

        margin_used = trade.get("MarginUsed", "").lower()
        client_agreement = trade.get("ClientAgreement", "").lower()

        if margin_used == "yes" and client_agreement == "cashaccount":
            reason = (
                "Margin Use Not Authorized: 'MarginUsed=Yes' in a 'CashAccount'."
            )
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
    Writes the suspicious trades report to a specified CSV file.

    :param report: A list of dictionaries, each describing a suspicious trade.
    :param output_file: The file path where the CSV will be written.
    """
    fieldnames = ["TradeID", "Date", "Trader", "Security", "RuleID", "Reason"]
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for entry in report:
            writer.writerow(entry)


def main() -> None:
    """
    Main execution flow:
      1. Reads trades from 'trades.csv'
      2. Checks them against defined rules
      3. Writes a suspicious trades report to the appropriate file.
    """
    trades = read_trades("trades.csv")
    suspicious_report = check_rules(trades)

    # Choose the output path depending on whether we're in Docker
    if os.getenv("RUNNING_IN_DOCKER"):
        output_file = "/app/suspicious_trades_report.csv"  # Docker path
    else:
        output_file = "output/suspicious_trades_report.csv"  # Local path

    write_report(suspicious_report, output_file)
    print(f"Report generated: {output_file}")


if __name__ == "__main__":
    main()
