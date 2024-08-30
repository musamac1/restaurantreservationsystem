import streamlit as st
import sqlite3
import json
from datetime import datetime
import pandas as pd

# Load configuration from JSON file
def load_config(file_path):
    """Load configuration from a JSON file."""
    with open(file_path, 'r') as f:
        config = json.load(f)
    return config

# Load API key
config = load_config('config.json')
gemini_api_key = config.get("GEMINI_API_KEY")

if not gemini_api_key:
    raise ValueError("API key not found in configuration file. Please check your config.json file.")

# Configure genai with API key
import google.generativeai as genai
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-pro')

def get_gemini_response(prompt):
    """Get a response from the Gemini model."""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error: {str(e)}"

# Initialize chat history and state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "reservation_details" not in st.session_state:
    st.session_state.reservation_details = {
        "name": "",
        "phone": "",
        "email": "",
        "guests": "",
        "baby_seats": "",
        "date": "",
        "time": ""
    }
    st.session_state.current_step = "start"

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('reservations.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            email TEXT,
            guests TEXT,
            baby_seats TEXT,
            date TEXT,
            time TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Save reservation to SQLite
def save_reservation():
    conn = sqlite3.connect('reservations.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reservations (name, phone, email, guests, baby_seats, date, time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        st.session_state.reservation_details["name"],
        st.session_state.reservation_details["phone"],
        st.session_state.reservation_details["email"],
        st.session_state.reservation_details["guests"],
        st.session_state.reservation_details["baby_seats"],
        st.session_state.reservation_details["date"],
        st.session_state.reservation_details["time"]
    ))
    conn.commit()
    conn.close()
    st.success("Reservation saved!")

# Function to reset state for new reservation
def reset_reservation():
    st.session_state.reservation_details = {
        "name": "",
        "phone": "",
        "email": "",
        "guests": "",
        "baby_seats": "",
        "date": "",
        "time": ""
    }
    st.session_state.current_step = "start"
    st.session_state.messages = []

# Initialize database
init_db()

# Streamlit app
st.title("Restaurant Reservation Chatbot")

# Sidebar navigation
st.sidebar.title("Navigation")
selection = st.sidebar.radio("Go to", ["Home", "Reservation", "Menu", "View Reservations"])

if selection == "Home":
    reset_reservation()
    st.write("Welcome to the Restaurant Reservation Chatbot!")
    st.write("Use the sidebar to navigate to the Reservation or Menu sections.")
    
elif selection == "Reservation":
    if st.session_state.current_step == "start":
        st.write("To make a reservation, please follow the prompts.")
    
    # Chat input
    user_input = st.chat_input("You: ", key="user_input")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Reservation process handling
        if st.session_state.current_step == "start":
            if "reserve" in user_input.lower() or "reservation" in user_input.lower() or "yes" in user_input.lower() or "sure" in user_input:
                st.session_state.messages.append({"role": "assistant", "content": "Sure, I'd be happy to help with your reservation. First, can I have your name?"})
                st.session_state.current_step = "name"
            else:
                st.session_state.messages.append({"role": "assistant", "content":  "hi,my name is Dani. I am the assistant of fast food restuarant.and I am here to collect the reservation details. Do want to reserve table in our restaurant?"})
        
        elif st.session_state.current_step == "name":
            st.session_state.reservation_details["name"] = user_input
            st.session_state.messages.append({"role": "assistant", "content": f"Nice to meet you, {user_input}. What’s your phone number?"})
            st.session_state.current_step = "phone"
        
        elif st.session_state.current_step == "phone":
            st.session_state.reservation_details["phone"] = user_input
            st.session_state.messages.append({"role": "assistant", "content": "Got it! Could you please provide your email address?"})
            st.session_state.current_step = "email"
        
        elif st.session_state.current_step == "email":
            st.session_state.reservation_details["email"] = user_input
            st.session_state.messages.append({"role": "assistant", "content": "Great! How many guests will be attending?"})
            st.session_state.current_step = "guests"
        
        elif st.session_state.current_step == "guests":
            st.session_state.reservation_details["guests"] = user_input
            st.session_state.messages.append({"role": "assistant", "content": "Understood. How many baby seats do you need?"})
            st.session_state.current_step = "baby_seats"
        
        elif st.session_state.current_step == "baby_seats":
            st.session_state.reservation_details["baby_seats"] = user_input
            st.session_state.messages.append({"role": "assistant", "content": "What date would you like to make the reservation for?"})
            st.session_state.current_step = "date"
        
        elif st.session_state.current_step == "date":
            try:
                # Check if input is a valid date
                datetime.strptime(user_input, '%Y-%m-%d')
                st.session_state.reservation_details["date"] = user_input
                st.session_state.messages.append({"role": "assistant", "content": "Got it. What time would you like the reservation for?"})
                st.session_state.current_step = "time"
            except ValueError:
                st.session_state.messages.append({"role": "assistant", "content": "Please enter a valid date in YYYY-MM-DD format."})
        
        elif st.session_state.current_step == "time":
            try:
                # Check if input is a valid time
                datetime.strptime(user_input, '%H:%M')
                st.session_state.reservation_details["time"] = user_input
                save_reservation()
                st.session_state.messages.append({"role": "assistant", "content": "Your reservation has been confirmed! If you need anything else, just let me know."})
                st.session_state.current_step = "start"  # Reset to initial step for new reservations
            except ValueError:
                st.session_state.messages.append({"role": "assistant", "content": "Please enter a valid time in HH:MM format."})

    # Display chat history
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.write("You: " + message["content"])
        else:
            st.write("Bot: " + message["content"])

elif selection == "Menu":
    st.write("Here is our menu:")
    st.write("1. **Starter**: Soup, Salad")
    st.write("2. **Main Course**: Pasta, Steak, Vegetarian Dish")
    st.write("3. **Dessert**: Ice Cream, Cake")
    st.write("4. **Beverages**: Coffee, Tea, Soft Drinks")

    st.write("If you have any specific questions about the menu or need recommendations, feel free to ask!")

elif selection == "View Reservations":
    conn = sqlite3.connect('reservations.db')
    df = pd.read_sql_query("SELECT * FROM reservations", conn)
    conn.close()
    
    if not df.empty:
        st.write("### Reservation Details")
        st.dataframe(df)
    else:
        st.write("No reservations found.")

# Optional: Button to reset reservation state
if st.sidebar.button("Reset Reservation"):
    reset_reservation()
    st.sidebar.write("Reservation state has been reset.")
