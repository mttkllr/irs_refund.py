import os
import argparse
import getpass
import logging # Added for potential future use, though print will be conditional for now
from dotenv import load_dotenv, set_key
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Load environment variables from .env file
load_dotenv()

def save_to_env(data_to_save):
    """Saves the provided data to a .env file."""
    try:
        # Create .env if it doesn't exist, or overwrite existing keys
        # dotenv's set_key will create the file if it doesn't exist.
        env_path = os.path.join(os.getcwd(), ".env")
        
        # We need to store the user-friendly filing status name, not the ID
        # The get_user_data function will handle the mapping to ID.
        set_key(env_path, "SSN", data_to_save["ssn_raw"]) # Store raw SSN before stripping hyphens
        set_key(env_path, "TAX_YEAR", data_to_save["tax_year"])
        set_key(env_path, "FILING_STATUS", data_to_save["filing_status_name"]) # Store the name like SINGLE, MFJ
        set_key(env_path, "REFUND_AMOUNT", data_to_save["amount"])
        print(f"Successfully saved data to {env_path}")
        return True
    except Exception as e:
        print(f"Error saving data to .env file: {e}")
        return False

def get_user_data(args):
    """Gets user data from environment variables or prompts the user."""
    ssn_raw = os.getenv("SSN") # Store potentially hyphenated SSN for saving
    tax_year = os.getenv("TAX_YEAR")
    filing_status_name = os.getenv("FILING_STATUS") # Expecting SINGLE, MFJ, etc.
    refund_amount = os.getenv("REFUND_AMOUNT")

    data_entered_manually = False
    if not all([ssn_raw, tax_year, filing_status_name, refund_amount]):
        print("Could not find all required information in .env file or command line arguments. Please enter manually:")
        data_entered_manually = True
        # Use getpass for SSN input
        ssn_raw_input = getpass.getpass(prompt="Enter your Social Security Number (SSN) (XXX-XX-XXXX or XXXXXXXXX): ")
        while True:
            tax_year_input = input("Enter the tax year (e.g., 2024, 2023, 2022, 2021): ")
            if tax_year_input in ["2024", "2023", "2022", "2021"]:
                break
            print("Invalid tax year. Please choose from 2024, 2023, 2022, or 2021.")
        
        filing_status_options = {
            "1": "SINGLE", "2": "MFJ", "3": "MFS", "4": "HOH", "5": "QW"
        }
        print("Select your filing status:")
        print("  1. SINGLE (Single)")
        print("  2. MFJ    (Married Filing Jointly)")
        print("  3. MFS    (Married Filing Separately)")
        print("  4. HOH    (Head of Household)")
        print("  5. QW     (Qualifying Widow(er))")
        
        while True:
            status_choice = input(f"Enter the number for your filing status (1-{len(filing_status_options)}): ")
            if status_choice in filing_status_options:
                filing_status_name_input = filing_status_options[status_choice]
                break
            print("Invalid selection. Please enter a valid number.")

        while True:
            refund_amount_input = input("Enter your expected refund amount (numbers only, e.g., 1234): ")
            if refund_amount_input.isdigit():
                break
            print("Invalid amount. Please enter numbers only.")
        
        # Update the variables if data was entered manually
        ssn = ssn_raw_input
        tax_year = tax_year_input
        filing_status_name = filing_status_name_input
        refund_amount = refund_amount_input
        
        # If save_env is flagged and data was entered manually, save it
        if args.save_env and data_entered_manually:
            print("\nWarning: Saving this information to the .env file will store your sensitive data")
            print("(SSN, Tax Year, Filing Status, Refund Amount) in plain text.")
            print("Ensure '.env' is listed in your .gitignore file to prevent accidental commits.\n")
            
            confirm_save = input("Do you want to save this information to the .env file? (yes/no): ").strip().lower()
            if confirm_save == 'yes':
                data_to_save = {
                    "ssn_raw": ssn, # Save the raw input ssn
                    "tax_year": tax_year,
                    "filing_status_name": filing_status_name, # Save the user-friendly name
                    "amount": refund_amount
                }
                save_to_env(data_to_save)
            else:
                print("Data not saved to .env file.")
    else: # Data was found in .env
        ssn = ssn_raw # Use the value from .env

    # Ensure ssn is processed for use with IRS site (remove hyphens)
    processed_ssn = ssn.replace("-", "") if ssn else ""

    # Map user-friendly filing status name to IRS website specific ID
    # Based on the provided HTML structure
    filing_status_id_map = {
        "SINGLE": "SINGLE",
        "MFJ": "MARRIED_FILING_JOINT",
        "MFS": "MARRIED_FILING_SEPARATE",
        "HOH": "HEAD_OF_HOUSEHOLD",
        "QW": "QUALIFYING_SURVIVING_SPOUSE"
    }
    filing_status_actual_id = filing_status_id_map.get(filing_status_name.upper())

    if not filing_status_actual_id:
        print(f"Error: Invalid FILING_STATUS \'{filing_status_name}\'. Please use one of: SINGLE, MFJ, MFS, HOH, QW, or check your .env file.")
        exit()

    return {
        "ssn": processed_ssn,
        "tax_year": tax_year, 
        "filing_status_id": filing_status_actual_id,
        "filing_status_name": filing_status_name, 
        "amount": refund_amount
    }

def check_irs_status(user_data, browser_choice, args):
    """Automates checking the IRS refund status using the specified browser."""
    
    driver = None
    if args.verbose:
        print(f"Using {browser_choice.capitalize()} browser.")

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"

    try:
        if browser_choice == "firefox":
            options = FirefoxOptions()
            options.add_argument("--headless")
            options.add_argument("--width=1080")
            options.add_argument("--height=1024")
            options.set_preference("general.useragent.override", user_agent)
            options.set_preference("dom.webdriver.enabled", False)
            options.set_preference('useAutomationExtension', False)
            if args.verbose:
                print("Initializing Firefox WebDriver...")
            service = FirefoxService(GeckoDriverManager().install())
            driver = webdriver.Firefox(service=service, options=options)
        elif browser_choice == "chrome":
            options = ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("window-size=1080,1024")
            options.add_argument(f"user-agent={user_agent}")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Check for custom Chrome binary path
            chrome_binary_path = os.getenv("CHROME_BINARY_PATH")
            if chrome_binary_path:
                if args.verbose:
                    print(f"Using custom Chrome binary path: {chrome_binary_path}")
                options.binary_location = chrome_binary_path
            
            if args.verbose:
                print("Initializing Chrome WebDriver...")
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', { get: () => false });
                    window.chrome = { runtime: {} };
                    if (navigator.permissions) {
                        const originalQuery = navigator.permissions.query;
                        navigator.permissions.query = (parameters) => (
                            parameters.name === 'notifications' ?
                                Promise.resolve({ state: Notification.permission }) :
                                originalQuery(parameters)
                        );
                    }
                """
            })
        elif browser_choice == "edge":
            options = EdgeOptions()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("window-size=1080,1024")
            options.add_argument(f"user-agent={user_agent}")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            if args.verbose:
                print("Initializing Edge WebDriver...")
            service = EdgeService(EdgeChromiumDriverManager().install())
            driver = webdriver.Edge(service=service, options=options)
            # Attempt to use CDP for Edge as it's Chromium-based
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', { get: () => false });
                    window.chrome = { runtime: {} }; // Edge might respond to window.chrome
                    if (navigator.permissions) {
                        const originalQuery = navigator.permissions.query;
                        navigator.permissions.query = (parameters) => (
                            parameters.name === 'notifications' ?
                                Promise.resolve({ state: Notification.permission }) :
                                originalQuery(parameters)
                        );
                    }
                """
            })
        else:
            print(f"Unsupported browser: {browser_choice}")
            return

        if args.verbose:
            print("Navigating to IRS website...")
        driver.get('https://sa.www4.irs.gov/wmr/')
        wait = WebDriverWait(driver, 20)

        if args.verbose:
            print("Filling out form...")
        # SSN Input
        if args.verbose:
            print("Waiting for SSN input...")
        ssn_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input#ssnInputControl")))
        ssn_input.send_keys(user_data["ssn"])
        if args.verbose:
            print("SSN entered.")

        # Tax Year Selection
        tax_year_label_for = user_data['tax_year']
        if args.verbose:
            print(f"Waiting for Tax Year LABEL (CSS selector: label[for='{tax_year_label_for}'])...")
        tax_year_label_selector = f"label[for='{tax_year_label_for}']"
        tax_year_label = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, tax_year_label_selector)))
        tax_year_label.click()
        if args.verbose:
            print("Tax Year selected by clicking label.")

        # Filing Status Selection
        filing_status_label_for = user_data['filing_status_id']
        if args.verbose:
            print(f"Waiting for Filing Status LABEL (CSS selector: label[for='{filing_status_label_for}'])...")
        filing_status_label_selector = f"label[for='{filing_status_label_for}']"
        filing_status_label = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, filing_status_label_selector)))
        filing_status_label.click()
        if args.verbose:
            print("Filing Status selected by clicking label.")

        # Refund Amount Input
        if args.verbose:
            print("Waiting for Refund Amount input...")
        refund_input = wait.until(EC.presence_of_element_located((By.NAME, "refundAmountInput")))
        refund_input.send_keys(user_data["amount"])
        if args.verbose:
            print("Refund Amount entered.")

        # Submit Button
        if args.verbose:
            print("Waiting for Submit button...")
        submit_button_id = "anchor-ui-0"
        submit_button = wait.until(EC.element_to_be_clickable((By.ID, submit_button_id)))
        if args.verbose:
            print("Submit button found. Clicking...")
        submit_button.click()
        if args.verbose:
            print("Submit button clicked.")
        
        if not args.verbose:
            print("\nProcessing, please wait...") # Message for non-verbose mode

        if args.verbose:
            print("Waiting for results...")
        try:
            # Priority to the "current-step" as it indicates progress
            status_element_selector = "li div.current-step"
            status_div = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, status_element_selector)))
            status_li = status_div.find_element(By.XPATH, "./parent::li") 
            status_text = status_li.text
            print(f"\n--- Refund Status ---\n{status_text.strip()}")
            print("--- End IRS Message ---") # New line added
        except TimeoutException:
            try:
                # If "current-step" isn't found, look for an alert message
                alert_content_selector = ".section-alert__content"
                alert_div = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, alert_content_selector)))
                alert_text = alert_div.text
                print(f"\n--- Message from IRS ---\n{alert_text.strip()}")
                print("--- End IRS Message ---") # New line added
            except TimeoutException:
                print("Could not determine refund status or find a message after submission (timeout).")
                print("--- End IRS Message ---") # Also adding here for consistency with timeout
        except Exception as e:
            print(f"An error occurred while trying to extract the status: {e}")
            if driver and args.debug: # Check for debug flag
                print("Attempting to save debug info for extraction error...")
                try:
                    screenshot_filename = "irs_debug_screenshot.png"
                    page_source_filename = "irs_debug_page.html"
                    driver.save_screenshot(screenshot_filename)
                    with open(page_source_filename, "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    print(f"Screenshot saved to {os.path.join(os.getcwd(), screenshot_filename)}")
                    print(f"Page source saved to {os.path.join(os.getcwd(), page_source_filename)}")
                except Exception as dbg_e:
                    print(f"Failed to save debug info: {dbg_e}")

    except TimeoutException as e:
        print(f"A timeout occurred: {e}")
        if driver and args.debug: # Check for debug flag
            print("Attempting to save debug info for page timeout...")
            try:
                screenshot_filename = "irs_debug_screenshot.png"
                page_source_filename = "irs_debug_page.html"
                driver.save_screenshot(screenshot_filename)
                with open(page_source_filename, "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print(f"Screenshot saved to {os.path.join(os.getcwd(), screenshot_filename)}")
                print(f"Page source saved to {os.path.join(os.getcwd(), page_source_filename)}")
            except Exception as dbg_e:
                print(f"Failed to save debug info: {dbg_e}")
    except NoSuchElementException as e:
        print(f"An element was not found on the page: {e}")
        if driver and args.debug: # Check for debug flag
            print("Attempting to save debug info for no such element...")
            try:
                screenshot_filename = "irs_debug_screenshot.png"
                page_source_filename = "irs_debug_page.html"
                driver.save_screenshot(screenshot_filename)
                with open(page_source_filename, "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print(f"Screenshot saved to {os.path.join(os.getcwd(), screenshot_filename)}")
                print(f"Page source saved to {os.path.join(os.getcwd(), page_source_filename)}")
            except Exception as dbg_e:
                print(f"Failed to save debug info: {dbg_e}")
    except Exception as e:
        print(f"An unexpected error occurred with {browser_choice}: {e}")
        if driver and args.debug: # Check for debug flag
            print("Attempting to save debug info for unexpected error...")
            try:
                screenshot_filename = "irs_debug_screenshot.png"
                page_source_filename = "irs_debug_page.html"
                driver.save_screenshot(screenshot_filename)
                with open(page_source_filename, "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print(f"Screenshot saved to {os.path.join(os.getcwd(), screenshot_filename)}")
                print(f"Page source saved to {os.path.join(os.getcwd(), page_source_filename)}")
            except Exception as dbg_e:
                print(f"Failed to save debug info: {dbg_e}")
    finally:
        if driver:
            if args.debug: # Also save debug info just before quitting if debug is on
                print("Attempting to save final debug info before quitting...")
                try:
                    screenshot_filename = "irs_final_debug_screenshot.png"
                    page_source_filename = "irs_final_debug_page.html"
                    driver.save_screenshot(screenshot_filename)
                    with open(page_source_filename, "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    print(f"Final screenshot saved to {os.path.join(os.getcwd(), screenshot_filename)}")
                    print(f"Final page source saved to {os.path.join(os.getcwd(), page_source_filename)}")
                except Exception as dbg_e:
                    print(f"Failed to save final debug info: {dbg_e}")
            if args.verbose:
                print("Quitting browser...")
            driver.quit()

def main():
    parser = argparse.ArgumentParser(description="Check IRS Refund Status.")
    parser.add_argument(
        "--browser", 
        choices=["firefox", "chrome", "edge"], 
        default="chrome", 
        help="Specify the browser to use (firefox, chrome, edge). Default is chrome."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (saves screenshot and page source on error or at the end)."
    )
    parser.add_argument(
        "--save-env",
        action="store_true",
        help="Save the entered information to a .env file if not already present or if entered manually."
    )
    
    # Allow overriding .env values with command-line arguments (optional enhancement, not fully implemented here yet)
    # parser.add_argument("--ssn", help="Social Security Number")
    # parser.add_argument("--tax-year", help="Tax Year")
    # parser.add_argument("--filing-status", help="Filing Status (SINGLE, MFJ, etc.)")
    # parser.add_argument("--amount", help="Refund Amount")

    args = parser.parse_args()

    if args.verbose:
        print("Starting IRS Refund Checker script...")
        print(f"Arguments: {args}")

    user_data = get_user_data(args) 
    if user_data:
        if not args.verbose: # New message before browser interaction starts
            print("\nPreparing to check your refund status, please wait...")
        check_irs_status(user_data, args.browser, args) 
    else:
        if args.verbose:
            print("Could not retrieve user data. Exiting.")

if __name__ == "__main__":
    main() 