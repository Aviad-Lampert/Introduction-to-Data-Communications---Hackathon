import socket
import threading
import time
import struct
import random
from colorama import Fore, Style  # To manage colored text

from util import MAGIC_COOKIE, OFFER_MESSAGE_TYPE, REQUEST_MESSAGE_TYPE, PAYLOAD_MESSAGE_TYPE

class Client:
    def __init__(self):
        self.server_ip = None
        self.tcp_port = None
        self.udp_port = None
        self.file_size = 0
        self.tcp_connections = 0
        self.udp_connections = 0

    def start(self):
        self.get_user_input()
        print("Client started, listening for offer requests...")
        self.listen_for_offers()

    def get_user_input(self):
        try:
            self.file_size = int(input("Enter the file size (in bytes): "))
            self.tcp_connections = int(input("Enter the number of TCP connections: "))
            self.udp_connections = int(input("Enter the number of UDP connections: "))
        except ValueError:
            print("Invalid input. Please enter numeric values.")
            self.get_user_input()

    def listen_for_offers(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(("", 13117))
            while True:
                data, addr = sock.recvfrom(1024)
                if len(data) < 9:
                    continue
                cookie, message_type, udp_port, tcp_port = struct.unpack('!IBHH', data[:9])
                if cookie != MAGIC_COOKIE or message_type != OFFER_MESSAGE_TYPE:
                    continue

                self.server_ip = addr[0]
                self.udp_port = udp_port
                self.tcp_port = tcp_port

                print(f"Received offer from {self.server_ip}")
                self.speed_test()

    def speed_test(self):
        tcp_threads = []
        udp_threads = []

        for index in range(self.tcp_connections):
            tcp_thread = threading.Thread(target=self.tcp_transfer, args=(index,))
            tcp_threads.append(tcp_thread)
            tcp_thread.start()

        for index in range(self.udp_connections):
            udp_thread = threading.Thread(target=self.udp_transfer, args=(index,))
            udp_threads.append(udp_thread)
            udp_thread.start()

        for thread in tcp_threads + udp_threads:
            thread.join()

        print("\n" + "_" * 77)
        print("All transfers complete, listening to offer requests")

    def tcp_transfer(self, index):
        start_time = time.time()
        color = random.choice([Fore.RED, Fore.GREEN, Fore.BLUE, Fore.CYAN, Fore.MAGENTA, Fore.YELLOW])

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.server_ip, self.tcp_port))
                sock.sendall(f"{self.file_size}\n".encode())
                received_data = sock.recv(self.file_size)

            duration = time.time() - start_time
            if duration == 0:
                duration = 0.001  # Avoid division by zero
            speed = (len(received_data) * 8) / duration
            print(f"{color}[TCP-{index}] Transfer finished: Time: {duration:.2f}s, Speed: {speed:.2f} bits/s{Style.RESET_ALL}\n")
        except Exception as e:
            print(f"{color}[TCP-{index}] Error during transfer: {e}{Style.RESET_ALL}\n")

    def udp_transfer(self, index):
        start_time = time.time()
        segment_size = 1024
        total_segments = (self.file_size + segment_size - 1) // segment_size
        received_segments = 0
        color = random.choice([Fore.RED, Fore.GREEN, Fore.BLUE, Fore.CYAN, Fore.MAGENTA, Fore.YELLOW])

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.sendto(struct.pack('!IBQ', MAGIC_COOKIE, REQUEST_MESSAGE_TYPE, self.file_size),
                            (self.server_ip, self.udp_port))
                sock.settimeout(1)
                while True:
                    try:
                        data, _ = sock.recvfrom(2048)
                        cookie, message_type, total, current = struct.unpack('!IBQQ', data[:21])
                        if cookie != MAGIC_COOKIE or message_type != PAYLOAD_MESSAGE_TYPE:
                            continue
                        received_segments += 1
                    except socket.timeout:
                        break

            duration = time.time() - start_time
            if duration == 0:
                duration = 0.001  # Avoid division by zero
            speed = (received_segments * segment_size * 8) / duration
            success_rate = (received_segments / total_segments) * 100
            print(f"{color}[UDP-{index}] Transfer finished: Time: {duration:.2f}s, Speed: {speed:.2f} bits/s, Success: {success_rate:.2f}%{Style.RESET_ALL}\n")
        except Exception as e:
            print(f"{color}[UDP-{index}] Error during transfer: {e}{Style.RESET_ALL}\n")

if __name__ == "__main__":
    client = Client()
    client.start()