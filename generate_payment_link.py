import requests
import gspread
import os
from google.oauth2.service_account import Credentials
from datetime import datetime
from dotenv import load_dotenv

# ============ PAYSTACK SETUP ============
load_dotenv()

PAYSTACK_SECRET_KEY = os.environ.get("PAYSTACK_SECRET_KEY")  # swap to sk_live_ when ready

# ============ GOOGLE SHEETS SETUP ============
# This figures out the exact folder THIS script lives in, no matter
# what folder your terminal happens to be sitting in when you run it.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to the JSON key file, always looked up relative to this script's own folder
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "service_account_key.json")

SPREADSHEET_NAME = "The Cairn Co. spreadsheet"
WORKSHEET_NAME = "Payment Updates"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


def get_worksheet():
    """Connects to Google Sheets and returns the specific worksheet we want to write to."""
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open(SPREADSHEET_NAME)
    worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
    return worksheet


def ensure_headers(worksheet):
    """Adds header row if the sheet is currently empty."""
    existing_values = worksheet.get_all_values()
    if not existing_values:
        worksheet.append_row(["Date", "Customer Email", "Amount (NGN)", "Reference", "Status"])


def log_payment_to_sheet(email, amount_naira, reference):
    """Adds a new row to the sheet for this payment."""
    worksheet = get_worksheet()
    ensure_headers(worksheet)

    row = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        email,
        amount_naira,
        reference,
        "Pending"
    ]
    worksheet.append_row(row)
    print("Logged to Google Sheet successfully!")

def sync_pending_payments():
    worksheet = get_worksheet()
    all_rows = worksheet.get_all_values()
    if not all_rows:
        print("Sheet is empty, nothing to sync.")
        return
    header = all_rows[0]
    status_col_index = header.index("Status") + 1
    reference_col_index = header.index("Reference") + 1
    updated_count = 0
    for row_number, row in enumerate(all_rows[1:], start=2):
        status = row[status_col_index - 1]
        reference = row[reference_col_index - 1]
        if status != "Pending":
            continue
        real_status = check_transaction_status(reference)
        if real_status and real_status != "Pending":
            worksheet.update_cell(row_number, status_col_index, real_status)
            updated_count += 1
            print(f"Updated {reference}: {real_status}")
    print(f"Sync complete. {updated_count} row(s) updated.")


def generate_payment_link(email, amount_naira):
    """
    Generates a Paystack payment link for a given customer email and amount,
    then logs it to the Google Sheet.
    """
    url = "https://api.paystack.co/transaction/initialize"

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    amount_kobo = int(amount_naira * 100)

    data = {
        "email": email,
        "amount": amount_kobo
    }

    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    if result.get("status") is True:
        link = result["data"]["authorization_url"]
        reference = result["data"]["reference"]
        print("Payment link generated successfully!")
        print(f"Link: {link}")
        print(f"Reference: {reference}")

        # Now log it to the sheet
        log_payment_to_sheet(email, amount_naira, reference)

        return link, reference
    else:
        print("Something went wrong:")
        print(result.get("message"))
        return None, None


if __name__ == "__main__":
    customer_email = "oluwatetisimi17@gmail.com"
    amount = 2000  # in Naira

    generate_payment_link(customer_email, amount)
