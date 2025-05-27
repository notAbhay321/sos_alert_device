# sosv10_fixed.py

import RPi.GPIO as GPIO
import time
import smtplib
import requests
import serial
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from threading import Thread, Lock
import socket
from datetime import datetime
from PIL import Image

# --- GPIO SETUP ---
button_pin = 17  # GPIO17 (Pin 11)
buzzer_pin = 18  # GPIO18 (Pin 12)

GPIO.setmode(GPIO.BCM)
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(buzzer_pin, GPIO.OUT)

# --- EMAIL SETUP ---
sender_email = "iotprojectsosalert321@gmail.com"
receiver_email = "amoghwadikar@gmail.com"
app_password = "ytaf rttf gcwk fatf"
subject = "🚨 SOS ALERT"
body_template = """EMERGENCY ALERT!

🚨 I need immediate assistance!
📍 Location: {location_info}
🕒 Time: {timestamp}
📶 IP Address: {ip_address}

Google Maps: {google_maps_link}

This is an automated alert from my Raspberry Pi SOS device."""

# --- TELEGRAM SETUP ---
BOT_TOKEN = "7606896913:AAF-qQKNwlIgf4GEHyu2uZgE1osVSEFz87c"
CHAT_ID = "5994490090"

# --- GPS LOCK ---
gps_lock = Lock()

# --- GPS FUNCTIONS ---
def convert_to_decimal(degree_min, direction):
    """Convert NMEA coordinate format to decimal degrees"""
    if not degree_min:
        return 0.0
    degrees = int(float(degree_min) / 100)
    minutes = float(degree_min) - degrees * 100
    decimal = degrees + minutes / 60
    return -decimal if direction in ['S', 'W'] else decimal

def parse_gps_data(line):
    """Parse NMEA sentences and extract relevant data"""
    if line.startswith('$GNRMC') or line.startswith('$GPRMC'):
        parts = line.split(',')
        if len(parts) >= 10 and parts[2] == 'A':  # Valid position data
            return {
                'time': parts[1][:2] + ":" + parts[1][2:4] + ":" + parts[1][4:6],
                'lat': convert_to_decimal(parts[3], parts[4]),
                'lon': convert_to_decimal(parts[5], parts[6]),
                'speed': float(parts[7]) if parts[7] else 0.0,
                'course': float(parts[8]) if parts[8] else 0.0,
                'date': parts[9][:2] + "/" + parts[9][2:4] + "/20" + parts[9][4:6],
                'valid': True
            }
    return None

def get_gps_location(max_attempts=10, attempt_delay=1):
    """Get GPS location with multiple attempts and proper resource management"""
    location_info = "Location not available"
    google_maps_link = "Location not available"
    gps_data = None
    
    # Try multiple ports
    possible_ports = ['/dev/ttyS0', '/dev/serial0', '/dev/ttyAMA0']
    
    for port in possible_ports:
        try:
            with gps_lock:
                print(f"🔍 Trying GPS on {port}...")
                with serial.Serial(port, 115200, timeout=1) as ser:
                    print(f"📡 GPS connected on {port}, waiting for fix...")
                    
                    attempts = 0
                    while attempts < max_attempts:
                        try:
                            line = ser.readline().decode('ascii', errors='ignore').strip()
                            if not line:
                                continue
                                
                            data = parse_gps_data(line)
                            if data and 'valid' in data:
                                gps_data = data
                                location_info = (
                                    f"Coordinates: {data['lat']:.6f}°N, {data['lon']:.6f}°E\n"
                                    f"Time: {data['time']} UTC | Date: {data['date']}\n"
                                    f"Speed: {data['speed']:.1f} knots | Course: {data['course']:.1f}°"
                                )
                                google_maps_link = f"https://www.google.com/maps?q={data['lat']},{data['lon']}"
                                print("📍 GPS location acquired!")
                                return location_info, google_maps_link
                                
                        except Exception as e:
                            print(f"⚠ GPS read error: {str(e)}")
                            
                        attempts += 1
                        print(f"🔄 GPS attempt {attempts}/{max_attempts}")
                        time.sleep(attempt_delay)
                        
        except serial.SerialException as e:
            print(f"❌ Could not open {port}: {str(e)}")
            continue
            
    # Fallback to IP if GPS fails
    try:
        ip = get_ip_address()
        if ip != "IP not available":
            location_info = f"IP Address: {ip}\nApproximate location based on network"
            google_maps_link = f"https://www.google.com/maps/search/?api=1&query={ip}"
            print("🌐 Using IP-based location fallback")
    except Exception as e:
        print(f"⚠ IP location error: {str(e)}")
    
    return location_info, google_maps_link

def get_ip_address():
    """Get the device's IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "IP not available"

# --- CREATE BLANK IMAGE FUNCTION ---
def create_blank_image():
    """Create a blank white image named image.jpg"""
    try:
        # Create a blank white image (640x480 pixels)
        image = Image.new('RGB', (640, 480), color='white')
        image_file = "/home/pi/image.jpg"
        image.save(image_file, 'JPEG')
        print(f"📷 Blank image created: {image_file}")
        return image_file
    except Exception as e:
        print(f"📷 Error creating blank image: {str(e)}")
        return None

# --- IMAGE + TELEGRAM SEND ---
def send_images_with_location(location_info, google_maps_link):
    while True:
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Create blank image named image.jpg
            image_file = create_blank_image()
            
            if image_file is None:
                print("❌ Failed to create blank image")
                time.sleep(5)
                continue

            # Prepare message
            caption = f"""🚨 EMERGENCY ALERT! 🚨

📍 Location Information:
{location_info}

🕒 Time: {timestamp}
📌 Google Maps: {google_maps_link}

⚠ Please send help immediately!"""

            # Send to Telegram
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            with open(image_file, 'rb') as img:
                files = {'photo': img}
                data = {'chat_id': CHAT_ID, 'caption': caption}
                response = requests.post(url, files=files, data=data)
                print(f"📤 Telegram image sent (Status: {response.status_code})")

        except Exception as e:
            print(f"📱 Telegram error: {str(e)}")

        time.sleep(5)

# --- EMAIL FUNCTION ---
def send_emergency_email(location_info, google_maps_link):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ip_address = get_ip_address()
        
        body = body_template.format(
            location_info=location_info,
            timestamp=timestamp,
            ip_address=ip_address,
            google_maps_link=google_maps_link
        )

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.send_message(msg)
        server.quit()

        print("📧 SOS email sent successfully!")

    except Exception as e:
        print(f"📧 Email error: {str(e)}")

# --- MAIN ---
def main():
    print("📟 System armed. Waiting for SOS button press...")
    try:
        while True:
            if GPIO.input(button_pin) == GPIO.LOW:
                print("\n🚨 SOS Triggered!")
                
                # Activate buzzer immediately
                GPIO.output(buzzer_pin, GPIO.HIGH)
                
                # Get location information
                print("🛰 Attempting to get GPS location...")
                location_info, google_maps_link = get_gps_location(max_attempts=10, attempt_delay=1)
                
                # Send email with location
                print("📧 Sending emergency email...")
                send_emergency_email(location_info, google_maps_link)
                
                # Send initial Telegram message
                print("📱 Sending initial Telegram alert...")
                try:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    initial_message = f"""🚨 EMERGENCY ALERT! 🚨

📍 Location Information:
{location_info}

🕒 Time: {timestamp}
📌 Google Maps: {google_maps_link}

⚠ Emergency button pressed! Starting live updates..."""
                    
                    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                    data = {'chat_id': CHAT_ID, 'text': initial_message}
                    response = requests.post(url, data=data)
                    print(f"📤 Initial Telegram message sent (Status: {response.status_code})")
                except Exception as e:
                    print(f"📱 Initial Telegram message failed: {str(e)}")
                
                # Start sending images with location to Telegram
                print("📸 Starting blank image creation and Telegram updates...")
                Thread(target=send_images_with_location, args=(location_info, google_maps_link), daemon=True).start()
                
                # Keep system active
                while True:
                    time.sleep(1)
                    
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n🛑 Program interrupted by user.")

    finally:
        GPIO.output(buzzer_pin, GPIO.LOW)
        GPIO.cleanup()
        print("🔴 System shut down safely.")

if _name_ == '_main_':
    main()