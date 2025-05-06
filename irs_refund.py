import os
import argparse
import getpass
from dotenv import load_dotenv
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

def get_user_data():
    """Gets user data from environment variables or prompts the user."""
    ssn = os.getenv("SSN")
    tax_year = os.getenv("TAX_YEAR")
    # Read the user-friendly filing status, e.g., SINGLE, MFJ
    filing_status_name = os.getenv("FILING_STATUS")
    refund_amount = os.getenv("REFUND_AMOUNT")

    if not all([ssn, tax_year, filing_status_name, refund_amount]):
        print("Could not find all required information in .env file. Please enter manually:")
        # Use getpass for SSN input
        ssn = getpass.getpass(prompt="Enter your Social Security Number (SSN) (XXX-XX-XXXX or XXXXXXXXX): ")
        while True:
            tax_year = input("Enter the tax year (e.g., 2024, 2023, 2022, 2021): ")
            if tax_year in ["2024", "2023", "2022", "2021"]:
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
                filing_status_name = filing_status_options[status_choice]
                break
            print("Invalid selection. Please enter a valid number.")

        while True:
            refund_amount = input("Enter your expected refund amount (numbers only, e.g., 1234): ")
            if refund_amount.isdigit():
                break
            print("Invalid amount. Please enter numbers only.")

    ssn = ssn.replace("-", "")

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
        print(f"Error: Invalid FILING_STATUS '{filing_status_name}'. Please use one of: SINGLE, MFJ, MFS, HOH, QW.")
        exit()

    return {
        "ssn": ssn,
        "tax_year": tax_year, # e.g., "2023"
        "filing_status_id": filing_status_actual_id, # e.g., "tc1"
        "filing_status_name": filing_status_name, # e.g., "SINGLE" for display
        "amount": refund_amount
    }

def check_irs_status(user_data, browser_choice):
    """Automates checking the IRS refund status using the specified browser."""
    
    driver = None
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

        print("Navigating to IRS website...")
        driver.get('https://sa.www4.irs.gov/wmr/')
        wait = WebDriverWait(driver, 20)

        print("Filling out form...")
        print("Waiting for SSN input...")
        ssn_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input#ssnInputControl")))
        ssn_input.send_keys(user_data["ssn"])
        print("SSN entered.")

        tax_year_label_for = user_data['tax_year'] # The 'for' attribute of the label matches the year (ID of input)
        print(f"Waiting for Tax Year LABEL (CSS selector: label[for='{tax_year_label_for}'])...")
        tax_year_label_selector = f"label[for='{tax_year_label_for}']" # Selector for the label
        tax_year_label = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, tax_year_label_selector)))
        tax_year_label.click()
        print("Tax Year selected by clicking label.")

        filing_status_label_for = user_data['filing_status_id'] # This is the ID like MARRIED_FILING_JOINT
        print(f"Waiting for Filing Status LABEL (CSS selector: label[for='{filing_status_label_for}'])...")
        filing_status_label_selector = f"label[for='{filing_status_label_for}']"
        filing_status_label = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, filing_status_label_selector)))
        filing_status_label.click()
        print("Filing Status selected by clicking label.")

        print("Waiting for Refund Amount input...")
        refund_input = wait.until(EC.presence_of_element_located((By.NAME, "refundAmountInput")))
        refund_input.send_keys(user_data["amount"])
        print("Refund Amount entered.")

        print("Waiting for Submit button...")
        # Corrected: Submit button is an <a> tag with id 'anchor-ui-0'
        submit_button = wait.until(EC.element_to_be_clickable((By.ID, "anchor-ui-0")))
        print("Submit button found. Clicking...")
        submit_button.click()
        print("Submit button clicked.")

        print("Waiting for results...")
        try:
            status_element_selector = "li div.current-step"
            status_div = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, status_element_selector)))
            status_li = status_div.find_element(By.XPATH, "./parent::li") 
            status_text = status_li.text
            print(f"\n--- Refund Status ---\n{status_text.strip()}")
        except TimeoutException:
            try:
                alert_content_selector = ".section-alert__content"
                alert_div = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, alert_content_selector)))
                alert_text = alert_div.text
                print(f"\n--- Message from IRS ---\n{alert_text.strip()}")
            except TimeoutException:
                print("Could not determine refund status or find a message after submission (timeout).")
        except Exception as e:
            print(f"An error occurred while trying to extract the status: {e}")
            if driver:
                print("Attempting to save screenshot for extraction error...")
                try:
                    filename = f"irs_extraction_error_{browser_choice}.png"
                    driver.save_screenshot(filename)
                    print(f"Screenshot saved to {os.path.join(os.getcwd(), filename)}")
                except Exception as scr_e:
                    print(f"Failed to save screenshot: {scr_e}")

    except TimeoutException as e:
        print(f"A timeout occurred while interacting with the page. Element not found or page load issue. Error: {e}")
        if driver:
            print("Attempting to save screenshot for page timeout...")
            try:
                filename = f"irs_page_timeout_{browser_choice}.png"
                driver.save_screenshot(filename)
                print(f"Screenshot saved to {os.path.join(os.getcwd(), filename)}")
            except Exception as scr_e:
                print(f"Failed to save screenshot: {scr_e}")
    except NoSuchElementException as e:
        print(f"An element was not found on the page: {e}")
        if driver:
            print("Attempting to save screenshot for no such element...")
            try:
                filename = f"irs_no_element_{browser_choice}.png"
                driver.save_screenshot(filename)
                print(f"Screenshot saved to {os.path.join(os.getcwd(), filename)}")
            except Exception as scr_e:
                print(f"Failed to save screenshot: {scr_e}")
    except Exception as e:
        print(f"An unexpected error occurred with {browser_choice}: {e}")
        if driver:
            print("Attempting to save screenshot for unexpected error...")
            try:
                filename = f"irs_unexpected_error_{browser_choice}.png"
                driver.save_screenshot(filename)
                print(f"Screenshot saved to {os.path.join(os.getcwd(), filename)}")
            except Exception as scr_e:
                print(f"Failed to save screenshot: {scr_e}")
    finally:
        if driver:
            print("Closing browser...")
            driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check IRS refund status.")
    parser.add_argument("--browser", type=str, choices=["firefox", "chrome", "edge"], default="firefox",
                        help="Browser to use (firefox, chrome, edge). Default: firefox")
    args = parser.parse_args()

    user_data = get_user_data()
    print("\n--- User Data Received ---")
    print(f"SSN: ...{user_data['ssn'][-4:]}")
    print(f"Tax Year: {user_data['tax_year']}")
    print(f"Filing Status: {user_data['filing_status_name']} (ID: {user_data['filing_status_id']})")
    print(f"Refund Amount: ${user_data['amount']}")
    print("-------------------------")

    check_irs_status(user_data, args.browser) 