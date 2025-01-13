import socket
import threading
import time
import struct

from util import MAGIC_COOKIE, OFFER_MESSAGE_TYPE, REQUEST_MESSAGE_TYPE, PAYLOAD_MESSAGE_TYPE


class Server:
    def __init__(self, ip, broadcast_port, udp_port, tcp_port):
        self.ip = ip
        self.broadcast_port = broadcast_port  # Port for broadcasting
        self.udp_port = udp_port  # Port for listening to client UDP requests
        self.tcp_port = tcp_port  # Port for listening to client TCP requests
        self.clients = []

    def start(self):
        print(f"Server started, listening on IP address {self.ip}")
        threading.Thread(target=self.broadcast_offers).start()
        threading.Thread(target=self.start_tcp_server).start()
        threading.Thread(target=self.start_udp_server).start()

    def broadcast_offers(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Enable broadcasting
            offer_message = struct.pack('!IBHH', MAGIC_COOKIE, OFFER_MESSAGE_TYPE, self.udp_port, self.tcp_port)
            print(f"Broadcasting offers on UDP port {self.broadcast_port}")
            while True:
                try:
                    sock.sendto(offer_message, ('<broadcast>', self.broadcast_port))
                    time.sleep(1)
                except Exception as e:
                    print(f"Error broadcasting offer: {e}")

    def start_tcp_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.bind((self.ip, self.tcp_port))
            server_sock.listen()
            print(f"TCP server listening on port {self.tcp_port}")
            while True:
                conn, addr = server_sock.accept()
                threading.Thread(target=self.handle_tcp_client, args=(conn, addr)).start()

    def handle_tcp_client(self, conn, addr):
        try:
            print("recieved tcp packet")

            data = conn.recv(1024).decode().strip()
            file_size = int(data)
            payload = b"1" * file_size
            conn.sendall(payload)
        finally:
            conn.close()

    def start_udp_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_sock:
            server_sock.bind((self.ip, self.udp_port))
            print(f"UDP server listening on port {self.udp_port}")
            while True:
                data, addr = server_sock.recvfrom(1024)
                print("recieved udp packet")

                threading.Thread(target=self.handle_udp_client, args=(data, addr)).start()

    def handle_udp_client(self, data, addr):
        if len(data) < 13:
            return
        cookie, message_type, file_size = struct.unpack('!IBQ', data[:13])
        if cookie != MAGIC_COOKIE or message_type != REQUEST_MESSAGE_TYPE:
            return

        segment_size = 1024
        total_segments = (file_size + segment_size - 1) // segment_size

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_sock:
            for segment in range(total_segments):
                payload = struct.pack('!IBQQ', MAGIC_COOKIE, PAYLOAD_MESSAGE_TYPE, total_segments,
                                      segment) + b"X" * segment_size
                udp_sock.sendto(payload, addr)


if __name__ == "__main__":
    server = Server("127.0.0.1", 13117, 20001, 20002)
    server.start()


