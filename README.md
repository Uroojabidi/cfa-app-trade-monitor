# cfa-app-trade-monitor

## Trade Compliance Monitor

A Python-based tool to detect potential conflicts of interest and material nonpublic information (MNPI) usage in trading activity, based on CFA Institute standards and custom compliance rules.

## Features
- Analyzes trade records in CSV format
- Detects 25+ potential compliance violations (currently 10)
- Containerized solution using Docker
- Generates detailed suspicious activity reports
- Checks for front-running, MNPI usage, market manipulation, and suitability issues

## Requirements
- Docker 20.10+
- Python 3.9+ (optional for local execution)
- CSV files in specified format

## Project Structure
.
├── Dockerfile
├── run.sh
├── main.py
├── trades.csv
├── cfa_standards.csv
├── cfa_rules.csv
└── output/
└── suspicious_trades_report.csv

## Installation
1. Clone repository/create project directory
2. Create output directory:
   ```bash
   mkdir output
   ```

## Usage
1. Run the container:
   ```bash
   ./run.sh
   ```
2. Check output in output/suspicious_trades_report.csv


## Key Rules Checked
- Front-running (Employee trades before clients)
- MNPI: Unusually large trades without public news
- Restricted list violations
- Unauthorized margin usage
- Wash trades and spoofing patterns
- Suitability mismatches
- Best execution violations

## Customization

- Add/modify rules in cfa_rules.csv
- Extend check_rules() function in main.py
- Add new trade records to trades.csv

## Support
For bug reports or feature requests, please open an issue in the project repository.

Note: This is a demonstration system - always validate findings with human compliance officers before taking action.

## Input Files

### CFA_Rules.csv
This file contains 30 simplified rules referencing common themes from the CFA Institute’s Code of Ethics and Standards of Professional Conduct (e.g., insider trading, front-running, suitability, best execution, market manipulation). Each row has:

- RuleID: Unique numeric identifier.
- RuleName: Brief name for the rule.
- Condition: A simplified logic statement (pseudo-code) showing how you might detect a violation. (You would parse/interpret this in Python.)
- Description: A short explanation of why the rule matters.
 
Note: The (Field='Value') syntax is just a placeholder. Adjust to your actual data fields and logic in your code.

### Sample_Trades.csv
Below is a compact CSV with 13 hypothetical trades (both employees and clients) and multiple columns to illustrate potential triggers. You won’t necessarily use all columns for all rules; they’re here to demonstrate how you might store data relevant to different checks.

Tip: In a real project, you may have fewer columns, or store reference data (e.g., average volume, restricted list) in separate tables. But this single CSV can help you quickly test the logic.

```csv
Date,Trader,Trader_Type,Security,Volume,Price,Public_News,MarketPrice,AvgVolume,ClientSaid,Authorization,Family_Account,Restricted_List,SoftDollarBenefit,CommissionRate,ResearchReportPositive,ReportReleaseDate,TradeType,UpgradeReleaseDate,EarningsDay,SubsequentSellOff,SecurityPromoted,OrderType,CancelRate,Buyer,Seller,TradeTime,PriceMove,ClientAccount,Turnover,MarginUsed,ClientAgreement,OutsideBusiness,EmployerNotInformed,ReferralFeeReceived,ClientNotInformed,DifferentPricesForSameSecurity,ClientProfiles,CommissionOnlyPaidIfOutcome,InternalResearchUpgrade
2025-01-10,John Doe,Employee,ABC,500,50.00,No,49.90,200,Yes,None,Yes,,No,0.02,No,,,2025-01-10,No,No,No,Limit,10%,,,15:55,6%,FeeBased,3,No,CashAccount,Yes,No,No,No,No,No,No,No
2025-01-10,Jane Smith,Client,ABC,200,49.75,No,49.90,200,Yes,Yes,,,No,0.02,No,,,2025-01-10,No,No,No,Limit,10%,,,15:55,6%,FeeBased,3,No,CashAccount,,,No,No,No,No,No,No,No,No
2025-01-11,Emily Clark,Employee,XYZ,6000,10.25,No,10.20,2500,No,None,No,,No,0.05,No,,,No,No,No,Market,0%,,,10:00,0%,FeeBased,1,No,CashAccount,,,No,No,No,No,No,No,No,No
2025-01-11,Mark Lee,Client,XYZ,2000,10.30,Yes,10.20,2500,Yes,Yes,,,No,0.03,No,,,No,No,No,Market,0%,,,10:01,0%,FeeBased,1,No,CashAccount,,,No,No,No,No,No,No,No,No
2025-01-12,John Doe,Employee,ZZZ,100,15.00,No,15.10,100,No,Yes,No,ZZZ,No,0.02,Yes,2025-01-13,Buy,,No,No,No,Market,0%,,,11:00,0%,FeeBased,2,Yes,CashAccount,,,No,No,No,No,No,No,Yes,No
2025-01-12,Amy Wong,Client,ZZZ,200,15.05,No,15.10,100,No,Yes,,,No,0.02,No,,,No,No,No,Market,0%,,,11:01,0%,FeeBased,2,No,CashAccount,,,No,No,No,No,No,No,No,No
2025-01-13,John Doe,Employee,ABC,600,51.00,No,51.10,300,No,Yes,Yes,,No,0.02,No,,,Yes,No,No,Market,0%,,,09:30,0%,FeeBased,2,Yes,CashAccount,,,No,No,No,No,No,No,No,Yes
2025-01-13,Emily Clark,Employee,ABC,700,50.50,No,51.10,300,No,Yes,No,,No,0.02,No,,,Yes,No,No,Market,0%,,,09:31,0%,FeeBased,2,Yes,CashAccount,,,No,No,No,No,No,No,No,Yes
2025-01-13,Michael Brown,Client,ABC,800,51.05,No,51.10,300,No,Yes,,,No,0.02,No,,,Yes,No,No,Market,0%,,,09:32,0%,FeeBased,2,No,CashAccount,,,No,No,No,No,No,No,No,No
2025-01-13,John Doe,Employee,XYZ,3000,10.10,No,10.00,1500,No,Yes,No,,No,0.02,No,,,No,No,No,Limit,5%,,,15:58,6%,FeeBased,3,No,CashAccount,,,No,No,No,No,No,No,No,No
2025-01-14,Mark Lee,Client,XYZ,5000,10.15,No,10.10,1500,Yes,Yes,,,No,0.02,No,,,No,No,No,Limit,5%,,,15:59,6%,FeeBased,3,No,CashAccount,,,No,No,No,No,No,No,No,No
2025-01-15,Tom Adams,Employee,MNO,10000,20.00,No,19.50,2000,No,Yes,No,,Personal,0.10,No,,,No,No,No,Market,0%,,,09:00,0%,FeeBased,1,No,CashAccount,,,Yes,Yes,No,No,No,No,No,No
2025-01-15,Anna Kim,Client,MNO,2000,20.10,No,19.50,2000,No,Yes,,,No,0.02,No,,,No,No,No,Market,0%,,,09:01,0%,FeeBased,1,No,CashAccount,,,No,No,No,No,No,No,No,No
```

#### Quick Notes on Selected Columns
- Trader_Type: “Employee” or “Client.”
- Volume / AvgVolume: Use these to check if (Volume > 2 * AvgVolume).
- Public_News: “Yes” or “No,” used to check MNPI.
- Restricted_List: If it matches Security, you can flag rule #20.
- MarginUsed / ClientAgreement: If MarginUsed='Yes' but the account is CashAccount, that’s a possible breach (rule #25).
- Family_Account: If Yes, check conflict-of-interest rules.
- DateDiff: Not explicitly shown, but you can compare dates to see if trades occur on the same or next day (for front-running).
