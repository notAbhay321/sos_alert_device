# 🚨 SDM SOS Alert System

A Raspberry Pi-based emergency SOS device that triggers alerts via **Email** and **Telegram** with real-time GPS location when a physical button is pressed.

---

## 📋 Features

- **One-press SOS** — Physical button triggers the entire alert pipeline instantly
- **GPS Location** — Acquires real-time coordinates via serial GPS module; falls back to IP-based location if GPS is unavailable
- **Email Alert** — Sends a formatted emergency email with location, timestamp, and Google Maps link
- **Telegram Alerts** — Sends an initial text alert followed by periodic image updates with location info
- **Buzzer Feedback** — Activates a buzzer immediately on button press to confirm trigger
- **Threaded Architecture** — Telegram image updates run in a background thread so the main loop stays responsive

---

## 🛠 Hardware Requirements

| Component | Details |
|---|---|
| Raspberry Pi | Any model with GPIO support |
| Push Button | Connected to GPIO17 (Pin 11) |
| Buzzer | Connected to GPIO18 (Pin 12) |
| GPS Module | Serial, connected via `/dev/ttyS0`, `/dev/serial0`, or `/dev/ttyAMA0` |

---

## 📦 Dependencies

Install the required Python libraries:

```bash
pip install RPi.GPIO pyserial requests Pillow
```

> Standard library modules used: `smtplib`, `socket`, `threading`, `datetime`

---

## ⚙️ Configuration

Before running, update the following constants in `sosv10_fixed.py`:

```python
# Email
sender_email = "your_email@gmail.com"
receiver_email = "receiver_email@gmail.com"
app_password = "your_gmail_app_password"   # Use a Gmail App Password, not your login password

# Telegram
BOT_TOKEN = "your_telegram_bot_token"
CHAT_ID = "your_telegram_chat_id"
```

> **Note:** Gmail requires an [App Password](https://support.google.com/accounts/answer/185833) with 2FA enabled.

---

## 🚀 Usage

```bash
python3 sosv10_fixed.py
```

The system arms itself immediately and waits for the SOS button to be pressed.

### What happens on button press:
1. Buzzer activates instantly
2. GPS location is acquired (up to 10 attempts)
3. Emergency email is sent with location + Google Maps link
4. Initial Telegram message is sent
5. Periodic Telegram updates (with image) begin every 5 seconds

---

## 📁 Project Structure

```
sdm_sos_project/
│
├── sosv10_fixed.py      # Main application script
└── README.md            # Project documentation
```

---

## ⚠️ Notes

- The system enters an **infinite loop** after SOS is triggered to keep sending updates. Use `Ctrl+C` to stop.
- GPIO cleanup is handled safely on exit via a `finally` block.
- GPS tries multiple serial ports automatically before falling back to IP-based location.

---

## 📄 License

This project was built for educational/demo purposes as part of the SDM SOS project.
