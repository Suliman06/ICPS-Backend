# ICPS Backend

Backend system for the **Integrated Classroom Pulse System (ICPS)**. This service receives classroom feedback from Raspberry Pi Pico 2W student pods using MQTT, stores feedback events in SQLite, and exposes API endpoints for the teacher dashboard.

## Overview

ICPS allows students to send one of three feedback signals during a lesson:

- `understand`
- `slow_down`
- `help`

The backend receives these signals, validates them, stores them with timestamps, and provides summary data for the frontend dashboard.

## System Flow

Pico 2W Student Pod
        ↓
MQTT publish
        ↓
Mosquitto MQTT Broker
        ↓
MQTT Listener / Backend
        ↓
SQLite Database
        ↓
FastAPI Endpoints
        ↓
Teacher Dashboard

## Features

- MQTT listener for real-time feedback messages
- FastAPI backend for dashboard data
- SQLite storage for lessons and feedback events
- Support for `understand`, `slow_down` and `help` actions
- Class mood and summary endpoints
- Local deployment suitable for Raspberry Pi 5
- Minimal-data design using pseudonymous student IDs

## Technologies

- Python
- FastAPI
- Uvicorn
- SQLite
- MQTT
- Mosquitto
- paho-mqtt
- Raspberry Pi 5

## Example MQTT Payload

{
  "student_id": "student_01",
  "action": "help",
  "lesson_id": 1
}

Default topic:

classroom/feedback

## Setup

Clone the repository:

git clone https://github.com/Suliman06/ICPS-Backend
cd icps-backend

Create and activate a virtual environment:

python -m venv venv

Windows:

venv\Scripts\activate

Linux/macOS:

source venv/bin/activate

Install dependencies:

pip install -r requirements.txt

Run the FastAPI backend:

uvicorn main:app --reload

Run the MQTT listener:

python mqtt_listener.py

FastAPI documentation should be available at:

http://127.0.0.1:8000/docs

## MQTT Test Command

Publish a test message:

mosquitto_pub -h localhost -t "classroom/feedback" -m "{\"student_id\":\"student_01\",\"action\":\"help\",\"lesson_id\":1}"

Subscribe to the topic for debugging:

mosquitto_sub -h localhost -t "classroom/feedback" -v

## Database

The backend uses SQLite for local prototype storage.

Main tables:

- `lessons`
- `events`

The `events` table stores feedback records such as:

student_id | action | timestamp | lesson_id

## Privacy and Security Notes

This project is a prototype for educational research and demonstration.

Recommended precautions:

- Use pseudonymous student IDs.
- Do not store real student names unless necessary.
- Do not commit real classroom databases.
- Do not commit Wi-Fi passwords, API keys or `.env` files.
- Restrict access to the dashboard in future deployment.
- Add MQTT authentication before wider classroom use.

## Repository Links

Frontend repository:

https://github.com/Suliman06/ICPS-Frontend

Backend repository:

https://github.com/Suliman06/ICPS-Backend

## Dissertation Context

This backend forms part of the **Integrated Classroom Pulse System (ICPS)** final year project. The system investigates how low-cost IoT technology can support real-time classroom feedback, teacher awareness and inclusive participation.

## Author

**Suliman Belaid**  
BSc (Hons) Computer Science  
Integrated Classroom Pulse System (ICPS)

## License

MIT License
EOF
