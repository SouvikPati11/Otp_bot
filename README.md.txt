# Telegram WebApp OTP Buyer (5sim.net API)

This project implements a Telegram WebApp allowing users to purchase temporary virtual numbers for OTP verification using the 5sim.net API.

## Features

- Select country (default: India 🇮🇳)
- Choose service (e.g., Instagram, Telegram)
- Check price and availability via 5sim.net
- Purchase number using in-app balance
- Receive OTP and display it in-app
- Automatic refund to in-app balance if no OTP is received in 15 minutes (client-side timer initiates backend refund process)
- Track purchase history
- View current in-app balance

## Tech Stack

- **Frontend:** HTML, CSS, JavaScript
- **Telegram Integration:** Telegram WebApp SDK (`telegram-web-app.js`)
- **Backend:** Python (Flask)
- **Database:** SQLite (default, configurable to PostgreSQL)
- **API:** 5sim.net

## Project Structure