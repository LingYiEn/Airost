








import sqlite3
from flask import Flask, request, jsonify
import re
from twilio.twiml.messaging_response import MessagingResponse

# Initialize Flask app
app = Flask(__name__)

# SQLite Database connection function
def connect_db():
    return sqlite3.connect('inventory.db')  # Specify your DB file name

# Function to create the inventory table
def create_inventory_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT,
            category TEXT,
            status TEXT,
            date_received TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')  # Ensure consistent indentation
    conn.commit()
    conn.close()

# Call this function to ensure the table exists when the app starts
create_inventory_table()

# Function to insert the received message into the database
def save_message(item_name, category, status):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO inventory (item_name, category, status) 
        VALUES (?, ?, ?)
    ''', (item_name, category, status))
    conn.commit()
    conn.close()

# Function to parse the incoming message
def parse_message(message):
    """Extract item name, category, and status from the message using regex."""
    # Regex to match specific fields
    item_name_match = re.search(r"(?i)Item Name:\s*(.+)", message)
    category_match = re.search(r"(?i)Category:\s*(.+)", message)
    status_match = re.search(r"(?i)Status:\s*(.+)", message)

    # Extract values or default to None
    item_name = item_name_match.group(1).strip() if item_name_match else None
    category = category_match.group(1).strip() if category_match else None
    status = status_match.group(1).strip() if status_match else None

    return item_name, category, status


# Endpoint to receive WhatsApp messages via webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Retrieve incoming message details
        from_number = request.form.get('From')
        message_body = request.form.get('Body')

        # Debugging: Log incoming data
        print(f"Received message from {from_number}: {message_body}")

        # Parse the message to extract item name, category, and status
        item_name, category, status = parse_message(message_body)

        # Debugging: Log parsed details
        print(f"Parsed message: Item Name: {item_name}, Category: {category}, Status: {status}")

        # Validate extracted details and form response
        if item_name and category and status:
            save_message(item_name, category, status)  # Save to the database
            response_message = (
                f"Thank you! Here's what I recorded:\n"
                f"Item Name: {item_name}\n"
                f"Category: {category}\n"
                f"Status: {status}"
            )
        else:
            # Provide instructions for correct format if parsing fails
            response_message = (
                "Sorry, I couldn't understand your message. Please use this format:\n"
                "Item Name: <item_name>\nCategory: <category>\nStatus: <status>"
            )

        # Send response back via Twilio
        from twilio.twiml.messaging_response import MessagingResponse
        resp = MessagingResponse()
        resp.message(response_message)
        return str(resp)

    except Exception as e:
        # Handle unexpected errors
        print(f"Error: {e}")
        return "An error occurred.", 500


# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
