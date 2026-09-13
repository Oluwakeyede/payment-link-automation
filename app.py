import os
import requests
from dotenv import load_dotenv
load_dotenv()
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from flask import Flask, request, render_template_string

app = Flask(__name__)

# ============ PAYSTACK SETUP ============
# Read from environment variable, never hardcoded, safe for GitHub/Render
PAYSTACK_SECRET_KEY = os.environ.get("PAYSTACK_SECRET_KEY")

# ============ GOOGLE SHEETS SETUP ============
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "service_account_key.json")

SPREADSHEET_NAME = "The Cairn Co. spreadsheet"
WORKSHEET_NAME = "Payment Updates"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

FORM_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>The Cairn Co. - Payment Link Generator</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 500px; margin: 40px auto; padding: 0 20px; }
        h2 { color: #1a1a2e; }
        input { width: 100%; padding: 10px; margin: 8px 0; box-sizing: border-box; }
        button { background: #2ecc71; color: white; padding: 12px; border: none; width: 100%; font-size: 16px; cursor: pointer; }
        .result { margin-top: 20px; padding: 15px; background: #f0f0f0; word-break: break-all; }
        .error { color: red; }
    </style>
</head>
<body>
    <h2>The Cairn Co. - Generate Payment Link</h2>
    <form method="POST">
        <label>Customer Email</label>
        <input type="email" name="email" required>
        <label>Amount (NGN)</label>
        <input type="number" name="amount" required>
        <button type="submit">Generate Link</button>
    </form>
    {% if link %}
    <div class="result">
        <strong>Link:</strong> <a href="{{ link }}">{{ link }}</a><br>
        <strong>Reference:</strong> {{ reference }}
    </div>
    {% endif %}
    {% if error %}
    <div class="result error">{{ error }}</div>
    {% endif %}
</body>
</html>
"""


def get_worksheet():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open(SPREADSHEET_NAME)
    worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
    return worksheet


def ensure_headers(worksheet):
    expected_headers = ["Date", "Customer Email", "Amount (NGN)", "Reference", "Status"]
    first_row = worksheet.row_values(1)
    if first_row != expected_headers:
        worksheet.insert_row(expected_headers, index=1)


def log_payment_to_sheet(email, amount_naira, reference):
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


def generate_payment_link(email, amount_naira):
    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    amount_kobo = int(amount_naira * 100)
    data = {"email": email, "amount": amount_kobo}

    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    if result.get("status") is True:
        link = result["data"]["authorization_url"]
        reference = result["data"]["reference"]
        log_payment_to_sheet(email, amount_naira, reference)
        return link, reference, None
    else:
        return None, None, result.get("message", "Something went wrong")


@app.route("/", methods=["GET", "POST"])
def home():
    link = None
    reference = None
    error = None

    if request.method == "POST":
        email = request.form.get("email")
        amount = request.form.get("amount")
        try:
            amount_naira = float(amount)
            link, reference, error = generate_payment_link(email, amount_naira)
        except ValueError:
            error = "Please enter a valid amount."

    return render_template_string(FORM_PAGE, link=link, reference=reference, error=error)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
