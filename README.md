# IRS Refund Checker (Python)

This script is a Python recreation of the [irs_refund_checker by DutchRican](https://github.com/DutchRican/irs_refund_checker), originally written in TypeScript using Bun and Puppeteer.

This script checks the status of your U.S. federal tax refund using the IRS "Where's My Refund?" tool.

## Security and Privacy Disclaimer

**Please be aware that this script handles sensitive personal information, including your Social Security Number (SSN), tax filing status, and refund amount.**

This information is entered into the official IRS "Where's My Refund?" website (sa.www4.irs.gov) to check your refund status. While the script automates this process, you are responsible for:

*   **Understanding the Risks:** Be aware of the inherent risks of entering personal information online.
*   **Secure Environment:** Ensure you are running this script on a secure computer and network.
*   **Code Review (Recommended):** While this script is provided in good faith, you are encouraged to review the source code (`irs_refund.py`) to understand how your data is handled before running it, especially if you obtained it from an unofficial source.
*   **Protect Your `.env` File:** If you choose to use a `.env` file to store your information, remember that it contains highly sensitive data. Ensure this file is **never** committed to version control (e.g., Git) and is appropriately secured on your local machine. The provided `.gitignore` file should help prevent accidental commits if you are using Git.

By using this script, you acknowledge and accept these responsibilities.

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

    Create a `requirements.txt` file with the following content:
    ```text
    selenium
    python-dotenv
    webdriver-manager
    ```

    Then install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Create a `.env` file (Optional but Recommended):**
    To avoid entering your information every time, you can create a `.env` file in the root of the project with the following content:
    ```
    SSN=YOUR_SOCIAL_SECURITY_NUMBER
    TAX_YEAR=2024 # or other year like 2023, 2022, 2021
    FILING_STATUS=SINGLE # Options: SINGLE, MFJ (Married Filing Jointly), MFS (Married Filing Separately), HOH (Head of Household), QW (Qualifying Widow(er))
    REFUND_AMOUNT=YOUR_REFUND_AMOUNT
    # CHROME_BINARY_PATH=/path/to/your/chrome # Optional: For custom Chrome/Chromium binary locations
    ```
    Replace the placeholder values with your actual information. **Ensure this file is added to your `.gitignore` if you are using Git, to protect your sensitive data.**

## Usage

Run the script from your terminal.

```bash
python irs_refund.py [OPTIONS]
```

**Options:**

*   `--browser <browser_name>`: Specify the browser to use.
    *   Choices: `firefox`, `chrome`, `edge`.
    *   Default: `chrome`.
*   `-v`, `--verbose`: Enable verbose logging to see detailed steps of the script's execution.
*   `--debug`: Enable debug mode. If an error occurs or at the end of the script, it will save a screenshot (`irs_debug_screenshot.png` or `irs_final_debug_screenshot.png`) and the page source (`irs_debug_page.html` or `irs_final_debug_page.html`) to the current directory.
*   `--save-env`: If you enter your information manually (because it's not in `.env` or you want to override), this flag will save/update the entered details to your `.env` file.

If the `--browser` flag is omitted, it will default to `chrome`.

**Examples:**

```bash
# Use Chrome (default)
python irs_refund.py

# Use Firefox
python irs_refund.py --browser firefox

# Use Edge
python irs_refund.py --browser edge

# Run with verbose output
python irs_refund.py --verbose

# Run in debug mode
python irs_refund.py --debug

# Enter details manually and save them to .env
python irs_refund.py --save-env
```

If you haven't created a `.env` file (or if it's missing some information), the script will prompt you to enter your SSN, tax year, filing status, and refund amount.
If you use the `--save-env` flag, this manually entered information will be saved to `.env` for future use.

The script will then launch a browser, navigate to the IRS website, fill in your information, and print the refund status to the console.

## Important Notes

*   **Maximum Daily Attempts:** The IRS website limits the number of times you can check your refund status per day. The exact number of attempts is not specified, but it is relatively small. If you exceed this limit, you will see a message like:
    ```
    --- Message from IRS ---
    Maximum attempts exceeded
    You have exceeded the number of maximum attempts. Please try again tomorrow.
    Note: Information is updated daily, usually overnight.
    --- End IRS Message ---
    ```
    If you encounter this, you will need to wait until the next day to check again.
*   **Data Storage**: If you choose to save your information to the `.env` file, be aware that your SSN, tax year, filing status, and refund amount will be stored in plain text. Ensure that `.env` is included in your `.gitignore` file to prevent accidental commits of sensitive data.
*   **Browser Drivers**: The script uses `webdriver-manager` to automatically download and manage browser drivers. If you encounter issues, ensure you have the chosen browser (Firefox, Chrome, or Edge) installed and that `webdriver-manager` can access the internet to download the appropriate driver.
*   **IRS Website Changes**: The IRS website structure or element IDs may change, which could break this script. If you encounter issues, please check the [IRS "Where's My Refund?" page](https://www.irs.gov/refunds) directly and consider opening an issue or pull request if you can identify the necessary changes. 