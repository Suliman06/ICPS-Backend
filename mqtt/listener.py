import json
import threading
import paho.mqtt.client as mqtt

from database.database import insert_event

MQTT_BROKER = "192.168.0.100"
MQTT_PORT = 1883
MQTT_TOPIC = "classroom/feedback"


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT listener connected")
        client.subscribe(MQTT_TOPIC)
        print(f"Subscribed to {MQTT_TOPIC}")
    else:
        print(f"MQTT connection failed with code {rc}")


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
        data = json.loads(payload)

        student_id = data.get("id")
        action = data.get("msg")

        if not student_id or not action:
            print("Invalid message format:", data)
            return

        insert_event(student_id=student_id, action=action)
        print(f"Stored event: {student_id} -> {action}")

    except Exception as e:
        print("Error processing MQTT message:", e)


def start_listener():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()


def start_listener_in_thread():
    thread = threading.Thread(target=start_listener, daemon=True)
    thread.start()
    return thread