# Payment Link Automation

A Python-based system that generates Paystack payment links on demand and automatically logs every transaction to Google Sheets, built to solve a real problem for my own small business, The Cairn Co.

## The Problem

I started a new business and didn't want to open a new business bank account, or mix it with my personal account. I'd already used Paystack as a customer on platforms like Chowdeck and others, and genuinely liked the payment options, the clean interface, and features like fraud prevention and secure payments. So instead of going back to a traditional bank account, Paystack felt like the right foundation to build on.

But once I explored the business side, I ran into a real problem: there was no way to generate one general, reusable payment link. The only option was creating a fresh link manually from the dashboard every single time I had a paying customer, which wasn't sustainable for how I actually wanted to run my business.

Paystack does have tools for handling multiple products and discounts, Storefronts, multi-product Payment Pages, but they're built for customers browsing a website. My customers order through direct messages, WhatsApp, Instagram, where they've already told me exactly what they want in plain conversation. There was no way to turn that into one payment link without first manually recreating their order in a storefront.

## The Solution

I'm not a software engineer, but I'm technically capable enough to work with Python and APIs. So I built my own solution:

- **`generate_payment_link.py`** — a script that calls Paystack's Transaction Initialize API directly to generate a payment link on demand, for any amount, without touching the Paystack dashboard.
- **Google Sheets integration** — every generated link is automatically logged (date, customer email, amount, reference, status) to a Google Sheet, using a Google Cloud service account for secure, no-login-required access.
- **`app.py`** — a Flask web app wrapping the same logic in a simple browser-based form, so it's usable from a phone or any device on the same network, not just from a terminal.

Every payment starts logged as **Pending**, and is only ever marked otherwise once genuinely confirmed, so the system never assumes a generated link means a completed sale.

## Tested With Real, Live Transactions

This isn't just a proof of concept. I tested the full system end-to-end using real, live Paystack transactions, generating a link, completing payment, and confirming it settled correctly to my bank account and logged accurately in the Sheet.

## Tech Stack

- Python
- Flask
- Paystack API
- Google Sheets API + Google Cloud Service Account (via `gspread`)
- `python-dotenv` for local environment variable management

## Security Notes

- API keys and credentials are never hardcoded. `PAYSTACK_SECRET_KEY` is read from an environment variable, and the Google service account key is excluded from version control via `.gitignore`.
- Test and live Paystack keys are kept fully separate throughout development.

## What's Next

- Deploying this to a hosted environment (Render) so it's accessible from anywhere, not just a local network.
- Adding a webhook listener so payments made through any channel, not just this tool, are automatically caught and logged.

## Why This Matters

While researching this further, I learned Paystack does support pre-filling an amount into a Payment Page URL, and even locking it as read-only. Technically, that means a single link could be reused with a different amount each time, without generating a new one from the dashboard.

But Paystack's own documentation acknowledges that tech-savvy customers can still notice and change values from the URL, which is exactly why they recommend the read-only lock in the first place. Even then, URL parameters remain a well-documented, tamperable point in web security more broadly. My solution avoids this entirely: the amount is set server-side, at the moment of generation, never exposed as something a customer could see or edit in a URL at all.

Beyond the security angle, that workaround still requires manually editing a URL for every single order. It doesn't calculate a total from multiple items, doesn't log anything automatically, and still depends on repetitive manual work. The real gap isn't that no workaround exists at all, it's that turning an actual conversation, "3 watches and a bag", into an accurate, secure, logged payment still requires real manual effort unless you're able to build your own way around it.

The gap underneath all of this: I could only build this because I happen to have technical skills most small business owners simply don't have. Paystack itself is accessible, but working around this specific limitation currently requires knowing how to code. That's the problem I'm continuing to think about solving, not just for myself, but for other small business owners in the same position.

## Built With AI-Assisted Development

This project was built using AI as a genuine technical collaborator, for writing, debugging, and extending the code, while I drove every decision about what problem to solve, how to solve it, and what tradeoffs to make. I'm not a trained software engineer, but I understand this system deeply enough to explain, defend, and extend it, which is exactly why I chose to disclose this openly rather than after the fact.
