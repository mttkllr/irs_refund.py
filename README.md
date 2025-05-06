# IRS Refund Checker (Python)

This script is a Python recreation of the [irs_refund_checker by DutchRican](https://github.com/DutchRican/irs_refund_checker), originally written in TypeScript using Bun and Puppeteer.

This script checks the status of your U.S. federal tax refund using the IRS "Where's My Refund?" tool.

## Prerequisites

- Python 3.x
- Pip (Python package installer)
- A supported web browser installed (Mozilla Firefox, Google Chrome, or Microsoft Edge).

## Setup

1.  **Clone the repository (or create the script):**
    ```bash
    # If you have a git repository
    # git clone <repository_url>
    # cd <repository_name>

    # Or, simply save the script as irs_refund.py
    ```

2.  **Install dependencies:**
    This script uses Selenium for browser automation. The necessary WebDriver 
    (GeckoDriver for Firefox, ChromeDriver for Chrome, or msedgedriver for Edge) 
    will be downloaded automatically by `webdriver-manager`.
    ```bash
    # Example using pip
    # pip install -r requirements.txt
    ```
    (We'll create `requirements.txt` later)

3.  **Create a `.env` file (Optional but Recommended):**
    To avoid entering your information every time, you can create a `.env` file in the root of the project with the following content:
    ```
    SSN=YOUR_SOCIAL_SECURITY_NUMBER
    TAX_YEAR=2024 # or other year like 2023, 2022, 2021
    FILING_STATUS=SINGLE # Options: SINGLE, MFJ (Married Filing Jointly), MFS (Married Filing Separately), HOH (Head of Household), QW (Qualifying Widow(er))
    REFUND_AMOUNT=YOUR_REFUND_AMOUNT
    ```
    Replace the placeholder values with your actual information. **Ensure this file is added to your `.gitignore` if you are using Git, to protect your sensitive data.**

## Usage

Run the script from your terminal. You can specify the browser using the `--browser` flag:

```bash
python irs_refund.py --browser <browser_name>
```

Replace `<browser_name>` with `firefox`, `chrome`, or `edge`.
If the `--browser` flag is omitted, it will default to `firefox`.

**Examples:**

```bash
# Use Firefox (default)
python irs_refund.py

# Use Chrome
python irs_refund.py --browser chrome

# Use Edge
python irs_refund.py --browser edge
```

If you haven't created a `.env` file, the script will prompt you to enter your SSN, tax year, filing status, and refund amount.

The script will then launch a browser, navigate to the IRS website, fill in your information, and print the refund status to the console. 