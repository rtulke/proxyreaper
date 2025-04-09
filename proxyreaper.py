#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proxy Reaper

This script checks a list of proxies for availability, speed, and anonymity.
It supports various protocols such as HTTP, HTTPS, SOCKS4, and SOCKS5.
Results can be saved as JSON, CSV, SQLite, or TXT, and fast proxies can be 
filtered and saved in a separate file.

The script supports configuration files at /etc/proxyreaper.conf and ~/.proxyreaper.conf,
automatic proxy list downloads, and provides detailed anonymity categorization.

Author: Robert Tulke
License: MIT
"""

# Application configuration
APP_NAME = "Proxy Reaper"
VERSION = "2.0.2"  # Version updated for optimization

import argparse
import requests
import socks
import socket
import time
import threading
import json
import csv
import re
import sys
import signal
import os
import sqlite3
import configparser
import hashlib
import concurrent.futures
import asyncio
import aiohttp
from pathlib import Path
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from colorama import init as colorama_init, Fore, Back, Style

# Initialize Colorama for ANSI color support (also on Windows)
colorama_init(autoreset=True)

# Global print lock to avoid garbled output from multiple threads
print_lock = threading.Lock()

# Global args variable to make debug flag accessible
global_args = None

# Global cache for GeoIP lookups (expanded for better performance)
geoip_cache = {}
dns_cache = {}  # New DNS cache to reduce DNS lookups

# Global results list and counter for autosave functionality
global_results = []
results_counter = 0
AUTOSAVE_FREQUENCY = 10  # Increased from 5 to 10 to reduce I/O overhead

# Integrated banner ASCII art without version info.
BANNER_TEXT = r"""

██▓███   ██▀███   ▒█████  ▒██   ██▒▓██   ██▓    ██▀███  ▓█████ ▄▄▄       ██▓███  ▓█████  ██▀███  
▓██░  ██▒▓██ ▒ ██▒▒██▒  ██▒▒▒ █ █ ▒░ ▒██  ██▒   ▓██ ▒ ██▒▓█   ▀▒████▄    ▓██░  ██▒▓█   ▀ ▓██ ▒ ██▒
▓██░ ██▓▒▓██ ░▄█ ▒▒██░  ██▒░░  █   ░  ▒██ ██░   ▓██ ░▄█ ▒▒███  ▒██  ▀█▄  ▓██░ ██▓▒▒███   ▓██ ░▄█ ▒
▒██▄█▓▒ ▒▒██▀▀█▄  ▒██   ██░ ░ █ █ ▒   ░ ▐██▓░   ▒██▀▀█▄  ▒▓█  ▄░██▄▄▄▄██ ▒██▄█▓▒ ▒▒▓█  ▄ ▒██▀▀█▄  
▒██▒ ░  ░░██▓ ▒██▒░ ████▓▒░▒██▒ ▒██▒  ░ ██▒▓░   ░██▓ ▒██▒░▒████▒▓█   ▓██▒▒██▒ ░  ░░▒████▒░██▓ ▒██▒
▒▓▒░ ░  ░░ ▒▓ ░▒▓░░ ▒░▒░▒░ ▒▒ ░ ░▓ ░   ██▒▒▒    ░ ▒▓ ░▒▓░░░ ▒░ ░▒▒   ▓▒█░▒▓▒░ ░  ░░░ ▒░ ░░ ▒▓ ░▒▓░
░▒ ░       ░▒ ░ ▒░  ░ ▒ ▒░ ░░   ░▒ ░ ▓██ ░▒░      ░▒ ░ ▒░ ░ ░  ░ ▒   ▒▒ ░░▒ ░      ░ ░  ░  ░▒ ░ ▒░
░░         ░░   ░ ░ ░ ░ ▒   ░    ░   ▒ ▒ ░░       ░░   ░    ░    ░   ▒   ░░          ░     ░░   ░ 
            ░         ░ ░   ░    ░   ░ ░           ░        ░  ░     ░  ░            ░  ░   ░     
                                     ░ ░                                                          
"""

# Default configuration values
DEFAULT_CONFIG = {
    'general': {
        'timeout': '5',
        'concurrent': '100',  # Increased default concurrency from 10 to 100
        'response_time_filter': '1000',
        'test_url': 'https://www.google.com',
        'chunk_size': '1000'  # New setting for batch processing
    },
    'output': {
        'format': 'json',
        'fast_only': 'false',
        'save_directory': 'results'
    },
    'proxysources': {
        'urls': ''  # Comma-separated list of URLs
    },
    'advanced': {
        'debug': 'false',
        'anonymity_check_url': 'https://httpbin.org/get',
        'use_async': 'true',  # New setting to enable async processing
        'autosave_batch': '100',  # New setting for autosave frequency
        'dns_cache_size': '1000'  # New setting for DNS cache size
    }
}

# Define anonymity levels with their colors
ANONYMITY_LEVELS = {
    "High Anonymous": {"color": "high_anonymous", "description": "Your IP and proxy status are hidden"},
    "Anonymous": {"color": "anonymous", "description": "Your IP is hidden but proxy is detected"},
    "Anonymous (Header leak)": {"color": "anonymous_header_leak", "description": "Your IP is hidden but proxy headers are visible"},
    "Transparent": {"color": "transparent", "description": "Your original IP is visible"},
    "Failed": {"color": "error", "description": "Could not determine anonymity level"}
}

# Global session for HTTP requests
http_session = None

# Global aiohttp session for async requests
aiohttp_session = None

# Semaphore for limiting concurrent connections
connection_semaphore = None

def initialize_sessions(concurrent_limit=100):
    """
    Initialize global HTTP sessions with connection pooling.
    
    Args:
        concurrent_limit (int): Maximum number of concurrent connections
        
    Returns:
        None
    """
    global http_session, connection_semaphore
    
    # Initialize requests session with connection pooling
    http_session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=concurrent_limit,
        pool_maxsize=concurrent_limit,
        max_retries=0
    )
    http_session.mount('http://', adapter)
    http_session.mount('https://', adapter)
    
    # Create semaphore for limiting concurrent connections
    # Anmerkung: aiohttp_session wird nur bei Bedarf (on-demand) erstellt
    connection_semaphore = None  # Wird erst bei Bedarf im async-Prozess erstellt

def clear_screen():
    print("\033c", end="")

def debug_print(message, level="info", lock=None):
    """
    Print messages with different colors based on level and respect debug flag.
    
    Args:
        message (str): The message to print
        level (str): The level of the message (info, success, warning, error, debug, etc.)
        lock (threading.Lock, optional): Lock to use for thread-safe printing
    
    Returns:
        None
    """
    if level == "debug" and (global_args is None or not global_args.debug):
        return
        
    colors = {
        "info": Fore.CYAN,
        "success": Fore.GREEN,
        "warning": Fore.YELLOW,
        "error": Fore.RED,
        "debug": Fore.MAGENTA,
        "high_anonymous": Fore.GREEN + Style.BRIGHT,
        "anonymous": Fore.BLUE + Style.BRIGHT,
        "anonymous_header_leak": Fore.YELLOW,
        "transparent": Fore.RED,
    }
    
    color = colors.get(level, Fore.WHITE)
    formatted_message = f"{color}{message}{Style.RESET_ALL}"
    
    if lock:
        with lock:
            print(formatted_message, flush=True)
    else:
        print(formatted_message, flush=True)

def display_banner():
    """
    Displays the integrated banner with a red gradient.
    After drawing the ASCII art, it prints the version info (highlighted in blue)
    right-aligned on a separate line.
    """
    lines = BANNER_TEXT.strip("\n").splitlines()
    total_lines = len(lines)
    # Determine the maximum width among the lines
    max_width = max(len(line.rstrip()) for line in lines)
    
    # Define a list of red shades using ANSI 256-color codes (from bright red to dark red)
    red_shades = [196, 160, 124, 88]
    for i, line in enumerate(lines):
        shade_index = int(i / total_lines * (len(red_shades) - 1))
        color_code = red_shades[shade_index]
        ansi_color = f"\033[38;5;{color_code}m"
        with print_lock:
            print(ansi_color + line.rstrip() + "\033[0m", flush=True)
    
    # Prepare version info right aligned to the banner width.
    version_str = f"{APP_NAME} v{VERSION}"
    padding = " " * (max_width - len(version_str)) if len(version_str) < max_width else ""
    with print_lock:
        print(padding + Fore.LIGHTBLACK_EX + Style.BRIGHT + version_str + Style.RESET_ALL, flush=True)

def load_config():
    """
    Load configuration from config files with priority:
    1. ~/.proxyreaper.conf
    2. /etc/proxyreaper.conf
    3. Default values
    
    Returns:
        configparser.ConfigParser: Loaded configuration
    """
    config = configparser.ConfigParser()
    
    # Set default values
    for section, options in DEFAULT_CONFIG.items():
        if not config.has_section(section):
            config.add_section(section)
        for key, value in options.items():
            config.set(section, key, value)
    
    # Check for system-wide config
    system_config = '/etc/proxyreaper.conf'
    if os.path.isfile(system_config):
        debug_print(f"Loading system config from {system_config}", "debug")
        config.read(system_config)
    
    # Check for user config (overrides system config)
    user_config = os.path.expanduser('~/.proxyreaper.conf')
    if os.path.isfile(user_config):
        debug_print(f"Loading user config from {user_config}", "debug")
        config.read(user_config)
    
    return config

def create_default_config(path):
    """
    Create a default configuration file at the specified path.
    
    Args:
        path (str): Path where to create the config file
    
    Returns:
        bool: True if successful, False otherwise
    """
    config = configparser.ConfigParser()
    
    for section, options in DEFAULT_CONFIG.items():
        config.add_section(section)
        for key, value in options.items():
            config.set(section, key, value)
    
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, 'w') as configfile:
            config.write(configfile)
        return True
    except Exception as e:
        debug_print(f"Error creating config file: {str(e)}", "error", print_lock)
        return False

def override_config_with_args(config, args):
    """
    Override configuration with command line arguments.
    
    Args:
        config (configparser.ConfigParser): Configuration to override
        args (argparse.Namespace): Command line arguments
    
    Returns:
        configparser.ConfigParser: Updated configuration
    """
    # Map of argument names to config sections and keys
    arg_map = {
        'timeout': ('general', 'timeout'),
        'concurrent': ('general', 'concurrent'),
        'response_time': ('general', 'response_time_filter'),
        'url': ('general', 'test_url'),
        'output': ('output', 'format'),
        'fast_only': ('output', 'fast_only'),
        'debug': ('advanced', 'debug')
    }
    
    for arg_name, (section, key) in arg_map.items():
        arg_value = getattr(args, arg_name, None)
        if arg_value is not None:
            if isinstance(arg_value, bool):
                arg_value = str(arg_value).lower()
            else:
                arg_value = str(arg_value)
            config.set(section, key, arg_value)
    
    return config

def resolve_hostname(hostname):
    """
    Resolve hostname to IP with caching to avoid repeated DNS lookups.
    
    Args:
        hostname (str): Hostname to resolve
        
    Returns:
        str: IP address or hostname if resolution failed
    """
    global dns_cache
    
    # If it's already an IP, return it
    if re.match(r'^(\d{1,3}\.){3}\d{1,3}$', hostname):
        return hostname
    
    # Check cache first
    if hostname in dns_cache:
        debug_print(f"DNS cache hit for {hostname}", "debug", print_lock)
        return dns_cache[hostname]
    
    try:
        debug_print(f"DNS lookup for {hostname}", "debug", print_lock)
        ip = socket.gethostbyname(hostname)
        dns_cache[hostname] = ip
        return ip
    except socket.gaierror:
        debug_print(f"DNS lookup failed for {hostname}", "debug", print_lock)
        return hostname

def get_public_ip():
    """
    Determines the user's actual public IP address using fallback services.
    
    Returns:
        str: Public IP address or "Unknown" if not found
    """
    global http_session
    services = [
        'https://api64.ipify.org?format=json',
        'https://ipinfo.io/json',
        'https://api.my-ip.io/ip.json',
        'https://api.ipify.org?format=json'
    ]
    
    for service in services:
        try:
            debug_print(f"Trying to get public IP from {service}", "debug", print_lock)
            response = http_session.get(service, timeout=5)
            if response.status_code == 200:
                data = response.json()
                for key in ["ip", "ip_addr", "origin"]:
                    ip = data.get(key)
                    if ip:
                        debug_print(f"Successfully retrieved public IP {ip} from {service}", "debug", print_lock)
                        return ip
        except (requests.RequestException, json.JSONDecodeError) as e:
            debug_print(f"Failed to get IP from {service}: {str(e)}", "debug", print_lock)
            continue
    
    debug_print("Could not determine public IP from any service", "warning", print_lock)
    return "Unknown"

async def get_public_ip_async():
    """
    Asynchronous version of get_public_ip().
    
    Returns:
        str: Public IP address or "Unknown" if not found
    """
    global aiohttp_session
    services = [
        'https://api64.ipify.org?format=json',
        'https://ipinfo.io/json',
        'https://api.my-ip.io/ip.json',
        'https://api.ipify.org?format=json'
    ]
    
    for service in services:
        try:
            debug_print(f"Trying to get public IP from {service}", "debug", print_lock)
            async with aiohttp_session.get(service, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    for key in ["ip", "ip_addr", "origin"]:
                        ip = data.get(key)
                        if ip:
                            debug_print(f"Successfully retrieved public IP {ip} from {service}", "debug", print_lock)
                            return ip
        except Exception as e:
            debug_print(f"Failed to get IP from {service}: {str(e)}", "debug", print_lock)
            continue
    
    debug_print("Could not determine public IP from any service", "warning", print_lock)
    return "Unknown"

def parse_proxies(proxy_input, auto_mode=False):
    """
    Parse proxy input which can be a single proxy, a comma-separated list,
    a file path, or URLs in automatic mode.
    
    Args:
        proxy_input (str): Input string containing proxies or a file path
        auto_mode (bool): Whether to download proxies from URLs
    
    Returns:
        list: List of parsed proxies
    """
    proxies = []
    
    # Handle automatic mode
    if auto_mode:
        debug_print("Automatic mode enabled, downloading proxy lists...", "info", print_lock)
        if not proxy_input:
            # Use URLs from config
            config = load_config()
            urls_str = config.get('proxysources', 'urls', fallback='')
            urls = [url.strip() for url in urls_str.split(',') if url.strip()]
        else:
            # Use URLs from command line
            urls = [url.strip() for url in proxy_input.split(',') if url.strip()]
        
        # Create a thread pool for downloading proxy lists
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for url in urls:
                futures.append(executor.submit(download_proxy_list, url))
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    url_proxies = future.result()
                    if url_proxies:
                        proxies.extend(url_proxies)
                except Exception as e:
                    debug_print(f"Error in proxy download thread: {str(e)}", "error", print_lock)
        
    # Handle standard file or comma-separated list
    elif ',' in proxy_input:
        proxies = [p.strip() for p in proxy_input.split(',') if p.strip()]
        debug_print(f"Parsed {len(proxies)} proxies from comma-separated input", "debug", print_lock)
    elif proxy_input.endswith('.txt'):
        try:
            with open(proxy_input, 'r', encoding='utf-8') as f:
                proxies = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
            debug_print(f"Loaded {len(proxies)} proxies from file {proxy_input}", "debug", print_lock)
        except FileNotFoundError:
            debug_print(f"File {proxy_input} not found.", "error", print_lock)
            sys.exit(1)
        except Exception as e:
            if global_args and global_args.debug:
                debug_print(f"Error reading file {proxy_input}: {str(e)}", "error", print_lock)
            else:
                debug_print(f"Error reading file {proxy_input}", "error", print_lock)
            sys.exit(1)
    else:
        proxies.append(proxy_input)
        debug_print(f"Using single proxy: {proxy_input}", "debug", print_lock)
    
    # Validate and normalize proxies
    valid_proxies = validate_proxies(proxies)
    
    if not valid_proxies:
        debug_print("No valid proxies found after validation.", "error", print_lock)
    
    return valid_proxies

def download_proxy_list(url):
    """
    Download a proxy list from a URL.
    
    Args:
        url (str): URL to download proxies from
        
    Returns:
        list: List of proxies
    """
    global http_session
    try:
        debug_print(f"Downloading proxies from {url}", "info", print_lock)
        response = http_session.get(url, timeout=10)
        if response.status_code == 200:
            content = response.text
            # Extract proxies from content (assumes one proxy per line)
            url_proxies = [line.strip() for line in content.splitlines() 
                          if line.strip() and not line.strip().startswith('#')]
            debug_print(f"Downloaded {len(url_proxies)} proxies from {url}", "success", print_lock)
            return url_proxies
        else:
            debug_print(f"Failed to download from {url}: HTTP {response.status_code}", "error", print_lock)
            return []
    except Exception as e:
        debug_print(f"Error downloading from {url}: {str(e)}", "error", print_lock)
        return []
    
def validate_proxies(proxies):
    """
    Validate and normalize proxy formats using parallel processing.
    
    Args:
        proxies (list): List of proxy strings to validate
    
    Returns:
        list: List of validated and normalized proxies
    """
    # Split into chunks for parallel processing
    chunk_size = 5000
    proxy_chunks = [proxies[i:i + chunk_size] for i in range(0, len(proxies), chunk_size)]
    
    valid_proxies = []
    invalid_proxies = []
    
    with ThreadPoolExecutor() as executor:
        futures = []
        for chunk in proxy_chunks:
            futures.append(executor.submit(validate_proxy_chunk, chunk))
        
        for future in concurrent.futures.as_completed(futures):
            try:
                valid_chunk, invalid_chunk = future.result()
                valid_proxies.extend(valid_chunk)
                invalid_proxies.extend(invalid_chunk)
            except Exception as e:
                debug_print(f"Error in validation thread: {str(e)}", "error", print_lock)
    
    # Log invalid proxies in debug mode
    if invalid_proxies:
        debug_print(f"Skipping {len(invalid_proxies)} invalid proxies:", "warning", print_lock)
        if global_args and global_args.debug:
            for proxy, reason in invalid_proxies[:10]:  # Show only first 10 in debug mode
                debug_print(f"  - {proxy}: {reason}", "debug", print_lock)
            if len(invalid_proxies) > 10:
                debug_print(f"  - ... and {len(invalid_proxies) - 10} more", "debug", print_lock)
    
    debug_print(f"Validated {len(valid_proxies)} proxies", "debug", print_lock)
    return valid_proxies

def validate_proxy_chunk(proxy_chunk):
    """
    Validate a chunk of proxies.
    
    Args:
        proxy_chunk (list): Chunk of proxies to validate
        
    Returns:
        tuple: (valid_proxies, invalid_proxies)
    """
    valid_proxies = []
    invalid_proxies = []
    
    for proxy in proxy_chunk:
        # Strip whitespace
        proxy = proxy.strip()
        
        # Skip empty lines
        if not proxy:
            continue
            
        # Check for protocol
        has_protocol = '://' in proxy
        
        if has_protocol:
            # Validate protocol://host:port format
            match = re.match(r'^(https?|socks[45])://(?:([^:@]+)(?::([^@]+))?@)?([^:]+):(\d+)/?$', proxy)
            if match:
                protocol, username, password, host, port = match.groups()
                
                # Validate port number
                try:
                    port_num = int(port)
                    if port_num < 1 or port_num > 65535:
                        invalid_proxies.append((proxy, "Port number out of valid range (1-65535)"))
                        continue
                except ValueError:
                    invalid_proxies.append((proxy, "Invalid port number"))
                    continue
                
                # Validate protocol
                if protocol not in ['http', 'https', 'socks4', 'socks5']:
                    invalid_proxies.append((proxy, f"Unsupported protocol: {protocol}"))
                    continue
                
                # Validate hostname
                if not re.match(r'^[a-zA-Z0-9.-]+$', host):
                    invalid_proxies.append((proxy, "Invalid hostname"))
                    continue
                
                # Rebuild the proxy with consistent format
                auth_part = f"{username}:{password}@" if username and password else ""
                valid_proxy = f"{protocol}://{auth_part}{host}:{port}"
                valid_proxies.append(valid_proxy)
            else:
                invalid_proxies.append((proxy, "Invalid format for proxy with protocol"))
        else:
            # Validate host:port format
            match = re.match(r'^([^:]+):(\d+)$', proxy)
            if match:
                host, port = match.groups()
                
                # Validate port number
                try:
                    port_num = int(port)
                    if port_num < 1 or port_num > 65535:
                        invalid_proxies.append((proxy, "Port number out of valid range (1-65535)"))
                        continue
                except ValueError:
                    invalid_proxies.append((proxy, "Invalid port number"))
                    continue
                
                # Validate hostname
                if not re.match(r'^[a-zA-Z0-9.-]+$', host):
                    invalid_proxies.append((proxy, "Invalid hostname"))
                    continue
                
                # Use http as default protocol
                valid_proxies.append(f"http://{host}:{port}")
            else:
                invalid_proxies.append((proxy, "Invalid format, expected host:port"))
    
    return valid_proxies, invalid_proxies

def sanitize_proxy(proxy):
    """
    Remove any unsafe characters from proxy string.
    
    Args:
        proxy (str): Proxy string to sanitize
    
    Returns:
        str: Sanitized proxy string
    """
    return re.sub(r'[^a-zA-Z0-9.:@/_-]', '', proxy)

def get_geoip_info(ip):
    """
    Get geographical information about an IP address.
    Uses caching to avoid repeated requests for the same IP.
    
    Args:
        ip (str): IP address to lookup
    
    Returns:
        tuple: (country, city) information
    """
    global geoip_cache, http_session
    
    # Check cache first
    if ip in geoip_cache:
        debug_print(f"GeoIP cache hit for {ip}", "debug", print_lock)
        return geoip_cache[ip]
    
    debug_print(f"GeoIP lookup for {ip}", "debug", print_lock)
    services = [
        {'url': f'https://ipinfo.io/{ip}/json', 'country_key': 'country', 'city_key': 'city'},
        {'url': f'https://freegeoip.app/json/{ip}', 'country_key': 'country_name', 'city_key': 'city'},
        {'url': f'https://ipapi.co/{ip}/json/', 'country_key': 'country_name', 'city_key': 'city'}
    ]
    
    for service in services:
        try:
            response = http_session.get(service['url'], timeout=5)
            if response.status_code == 200:
                data = response.json()
                country = data.get(service['country_key'], "Unknown")
                city = data.get(service['city_key'], "Unknown")
                
                # Cache the result
                geoip_cache[ip] = (country, city)
                
                debug_print(f"Got geo info for {ip}: {country}, {city}", "debug", print_lock)
                return country, city
        except (requests.RequestException, json.JSONDecodeError) as e:
            debug_print(f"Failed to get geo info from {service['url']}: {str(e)}", "debug", print_lock)
            continue
    
    # Cache the "Unknown" result to avoid repeated failures
    geoip_cache[ip] = ("Unknown", "Unknown")
    return "Unknown", "Unknown"

async def get_geoip_info_async(ip):
    """
    Asynchronous version of get_geoip_info.
    
    Args:
        ip (str): IP address to lookup
        
    Returns:
        tuple: (country, city) information
    """
    global geoip_cache, aiohttp_session, connection_semaphore
    
    # Check cache first
    if ip in geoip_cache:
        debug_print(f"GeoIP cache hit for {ip}", "debug", print_lock)
        return geoip_cache[ip]
    
    debug_print(f"GeoIP lookup for {ip}", "debug", print_lock)
    services = [
        {'url': f'https://ipinfo.io/{ip}/json', 'country_key': 'country', 'city_key': 'city'},
        {'url': f'https://freegeoip.app/json/{ip}', 'country_key': 'country_name', 'city_key': 'city'},
        {'url': f'https://ipapi.co/{ip}/json/', 'country_key': 'country_name', 'city_key': 'city'}
    ]
    
    for service in services:
        try:
            async with connection_semaphore:
                async with aiohttp_session.get(service['url'], timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        country = data.get(service['country_key'], "Unknown")
                        city = data.get(service['city_key'], "Unknown")
                        
                        # Cache the result
                        geoip_cache[ip] = (country, city)
                        
                        debug_print(f"Got geo info for {ip}: {country}, {city}", "debug", print_lock)
                        return country, city
        except Exception as e:
            debug_print(f"Failed to get geo info from {service['url']}: {str(e)}", "debug", print_lock)
            continue
    
    # Cache the "Unknown" result to avoid repeated failures
    geoip_cache[ip] = ("Unknown", "Unknown")
    return "Unknown", "Unknown"

def check_anonymity(proxy, anonymity_check_url, original_ip):
    """
    Checks if a proxy hides the IP address and evaluates its anonymity level.
    
    Args:
        proxy (str): Proxy to check
        anonymity_check_url (str): URL to use for checking anonymity
        original_ip (str): Original IP address for comparison
    
    Returns:
        tuple: (detected_ip, anonymity_level)
    """
    global http_session
    try:
        debug_print(f"Checking anonymity for {proxy}", "debug", print_lock)
        
        # Extended headers to check
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        response = http_session.get(
            anonymity_check_url, 
            proxies={"http": proxy, "https": proxy}, 
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            debug_print(f"Anonymity check failed with status code {response.status_code}", "debug", print_lock)
            return "Unknown", "Failed"
        
        try:
            data = response.json()
        except json.JSONDecodeError:
            debug_print(f"Anonymity check failed: Invalid JSON response", "debug", print_lock)
            return "Unknown", "Failed"
        
        proxy_ip = data.get("ip", data.get("origin", "Unknown"))
        headers_info = data.get("headers", {})
        
        # Convert header keys to case-insensitive dictionary
        headers_info = {k.lower(): v for k, v in headers_info.items()}
        
        # Log all headers in debug mode
        if global_args and global_args.debug:
            for header, value in headers_info.items():
                debug_print(f"Header: {header} = {value}", "debug", print_lock)
            
        # Check for original IP in any header (transparent proxy)
        for header, value in headers_info.items():
            if original_ip in str(value):
                debug_print(f"Transparent proxy detected - original IP leaked in {header} header", "debug", print_lock)
                return proxy_ip, "Transparent"
        
        # Check if proxy reveals itself via common headers
        proxy_headers = ["via", "proxy-connection", "forwarded", "x-forwarded"]
        reveals_proxy = False
        
        for header in headers_info:
            if any(ph in header.lower() for ph in proxy_headers):
                reveals_proxy = True
                debug_print(f"Proxy reveals itself via {header} header", "debug", print_lock)
                break
        
        # Determine anonymity level
        if proxy_ip != original_ip:
            if not reveals_proxy:
                # High anonymity: Different IP and no proxy headers
                debug_print(f"High anonymous proxy detected: {proxy_ip}", "debug", print_lock)
                return proxy_ip, "High Anonymous"
            else:
                # Regular anonymity: Different IP but proxy headers present
                debug_print(f"Anonymous proxy with header leak detected: {proxy_ip}", "debug", print_lock)
                return proxy_ip, "Anonymous (Header leak)"
        else:
            # Transparent: Same IP
            debug_print(f"Transparent proxy detected: {proxy_ip}", "debug", print_lock)
            return proxy_ip, "Transparent"
    
    except requests.RequestException as e:
        debug_print(f"Anonymity check exception: {str(e)}", "debug", print_lock)
        return "Unknown", "Failed"

async def check_anonymity_async(proxy, anonymity_check_url, original_ip):
    """
    Asynchronous version of check_anonymity.
    
    Args:
        proxy (str): Proxy to check
        anonymity_check_url (str): URL to use for checking anonymity
        original_ip (str): Original IP address for comparison
        
    Returns:
        tuple: (detected_ip, anonymity_level)
    """
    global aiohttp_session, connection_semaphore
    try:
        debug_print(f"Checking anonymity for {proxy}", "debug", print_lock)
        
        # Extended headers to check
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        # Parse proxy for aiohttp format
        parsed = urlparse(proxy)
        proxy_auth = ""
        if parsed.username and parsed.password:
            proxy_auth = f"{parsed.username}:{parsed.password}@"
        proxy_url = f"{parsed.scheme}://{proxy_auth}{parsed.hostname}:{parsed.port}"
        
        async with connection_semaphore:
            try:
                async with aiohttp_session.get(
                    anonymity_check_url,
                    proxy=proxy_url,
                    headers=headers,
                    timeout=10
                ) as response:
                    if response.status != 200:
                        debug_print(f"Anonymity check failed with status code {response.status}", "debug", print_lock)
                        return "Unknown", "Failed"
                    
                    try:
                        data = await response.json()
                    except Exception:
                        debug_print(f"Anonymity check failed: Invalid JSON response", "debug", print_lock)
                        return "Unknown", "Failed"
            except Exception as e:
                debug_print(f"Anonymity check request failed: {str(e)}", "debug", print_lock)
                return "Unknown", "Failed"
        
        proxy_ip = data.get("ip", data.get("origin", "Unknown"))
        headers_info = data.get("headers", {})
        
        # Convert header keys to case-insensitive dictionary
        headers_info = {k.lower(): v for k, v in headers_info.items()}
        
        # Log all headers in debug mode
        if global_args and global_args.debug:
            for header, value in headers_info.items():
                debug_print(f"Header: {header} = {value}", "debug", print_lock)
            
        # Check for original IP in any header (transparent proxy)
        for header, value in headers_info.items():
            if original_ip in str(value):
                debug_print(f"Transparent proxy detected - original IP leaked in {header} header", "debug", print_lock)
                return proxy_ip, "Transparent"
        
        # Check if proxy reveals itself via common headers
        proxy_headers = ["via", "proxy-connection", "forwarded", "x-forwarded"]
        reveals_proxy = False
        
        for header in headers_info:
            if any(ph in header.lower() for ph in proxy_headers):
                reveals_proxy = True
                debug_print(f"Proxy reveals itself via {header} header", "debug", print_lock)
                break
        
        # Determine anonymity level
        if proxy_ip != original_ip:
            if not reveals_proxy:
                # High anonymity: Different IP and no proxy headers
                debug_print(f"High anonymous proxy detected: {proxy_ip}", "debug", print_lock)
                return proxy_ip, "High Anonymous"
            else:
                # Regular anonymity: Different IP but proxy headers present
                debug_print(f"Anonymous proxy with header leak detected: {proxy_ip}", "debug", print_lock)
                return proxy_ip, "Anonymous (Header leak)"
        else:
            # Transparent: Same IP
            debug_print(f"Transparent proxy detected: {proxy_ip}", "debug", print_lock)
            return proxy_ip, "Transparent"
    
    except Exception as e:
        debug_print(f"Anonymity check exception: {str(e)}", "debug", print_lock)
        return "Unknown", "Failed"
    
def create_socket_connection(proxy_type, proxy_host, proxy_port, target_host, target_port, timeout):
    """
    Create a SOCKS connection to test SOCKS4/SOCKS5 proxies.
    
    Args:
        proxy_type (str): Type of proxy (socks4 or socks5)
        proxy_host (str): Proxy host address
        proxy_port (int): Proxy port number
        target_host (str): Target host to connect to
        target_port (int): Target port to connect to
        timeout (int): Connection timeout in seconds
    
    Returns:
        bool: True if connection was successful, False otherwise
    """
    debug_print(f"Testing {proxy_type} connection to {proxy_host}:{proxy_port}", "debug", print_lock)
    s = socks.socksocket()
    
    if proxy_type.lower() == "socks4":
        s.set_proxy(socks.SOCKS4, proxy_host, int(proxy_port))
    elif proxy_type.lower() == "socks5":
        s.set_proxy(socks.SOCKS5, proxy_host, int(proxy_port))
    else:
        debug_print(f"Unsupported proxy type: {proxy_type}", "debug", print_lock)
        return False
    
    s.settimeout(timeout)
    
    try:
        s.connect((target_host, int(target_port)))
        s.close()
        debug_print(f"SOCKS connection successful", "debug", print_lock)
        return True
    except Exception as e:
        debug_print(f"SOCKS connection failed: {str(e)}", "debug", print_lock)
        return False

async def create_socket_connection_async(proxy_type, proxy_host, proxy_port, target_host, target_port, timeout):
    """
    Asynchronous version of create_socket_connection.
    Uses asyncio to create a non-blocking socket connection.
    
    Args:
        proxy_type (str): Type of proxy (socks4 or socks5)
        proxy_host (str): Proxy host address
        proxy_port (int): Proxy port number
        target_host (str): Target host to connect to
        target_port (int): Target port to connect to
        timeout (int): Connection timeout in seconds
    
    Returns:
        bool: True if connection was successful, False otherwise
    """
    debug_print(f"Testing {proxy_type} connection to {proxy_host}:{proxy_port}", "debug", print_lock)
    
    # Use asyncio.to_thread to run the blocking socket operation in a separate thread
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        create_socket_connection,
        proxy_type, proxy_host, proxy_port, target_host, target_port, timeout
    )

def autosave_results(results, config, in_progress=True):
    """
    Automatically save results at regular intervals.
    
    Args:
        results (list): List of proxy check results
        config (configparser.ConfigParser): Configuration
        in_progress (bool): Whether this is an in-progress save or final
    
    Returns:
        None
    """
    global results_counter
    
    if not results:
        return
    
    # Submit the saving to a thread to avoid blocking the main thread
    save_thread = threading.Thread(
        target=autosave_results_thread,
        args=(results.copy(), config, in_progress)  # Copy results to avoid race conditions
    )
    save_thread.daemon = True
    save_thread.start()

def autosave_results_thread(results, config, in_progress=True):
    """
    Thread worker for saving results without blocking the main thread.
    
    Args:
        results (list): List of proxy check results
        config (configparser.ConfigParser): Configuration
        in_progress (bool): Whether this is an in-progress save or final
        
    Returns:
        None
    """
    # Create output directory
    save_dir = config.get('output', 'save_directory', fallback='results')
    os.makedirs(save_dir, exist_ok=True)
    
    # Generate timestamp and filename
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    status = "partial" if in_progress else "final"
    filename = f"{save_dir}/proxy_results_{timestamp}_{status}.json"
    
    # Save as JSON
    with open(filename, "w") as f:
        json.dump(results, f, indent=4)
    
    if in_progress:
        debug_print(f"Autosaved {len(results)} results to {filename}", "debug", print_lock)
    else:
        debug_print(f"Final results saved to {filename}", "success", print_lock)

def save_results(results, output_format, filter_fast=False, config=None):
    """
    Save results to files in the specified format.
    
    Args:
        results (list): List of proxy check results
        output_format (str): Format to save (json, csv, sqlite)
        filter_fast (bool): Whether to only save fast proxies
        config (configparser.ConfigParser): Configuration

    Returns:
        None
    """
    if not results:
        debug_print("No results available to save.", "error", print_lock)
        return
    
    # Start a thread to handle saving in the background
    save_thread = threading.Thread(
        target=save_results_thread,
        args=(results.copy(), output_format, filter_fast, config)  # Copy results to avoid race conditions
    )
    save_thread.daemon = True
    save_thread.start()
    
    # Return immediately so we don't block the main thread
    debug_print("Saving results in background thread...", "info", print_lock)

def save_results_thread(results, output_format, filter_fast=False, config=None):
    """
    Thread worker for saving results to files.
    
    Args:
        results (list): List of proxy check results
        output_format (str): Format to save (json, csv, sqlite)
        filter_fast (bool): Whether to only save fast proxies
        config (configparser.ConfigParser): Configuration
        
    Returns:
        None
    """
    # Create results directory
    save_dir = 'results' if not config else config.get('output', 'save_directory', fallback='results')
    os.makedirs(save_dir, exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # Filter fast proxies if requested
    if filter_fast:
        filtered_results = [r for r in results if r["status"] == "FAST"]
        file_prefix = "fast_proxies"
    else:
        filtered_results = results
        file_prefix = "proxy_results"
    
    # Optimize batch operations for faster file writing
    batch_size = 1000  # Process in chunks to reduce memory pressure
    
    if output_format == "json":
        filename = f"{save_dir}/{file_prefix}_{timestamp}.json"
        with open(filename, "w") as f:
            # Faster JSON serialization with less indentation for large datasets
            if len(filtered_results) > 5000:
                json.dump(filtered_results, f, indent=None)
            else:
                json.dump(filtered_results, f, indent=4)
        debug_print(f"Results saved as JSON: {filename}", "success", print_lock)
    
    elif output_format == "csv":
        filename = f"{save_dir}/{file_prefix}_{timestamp}.csv"
        with open(filename, "w", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["proxy", "status", "response_time", "country", "city", "anonymity", "protocol"])
            writer.writeheader()
            
            # Process in batches for better memory efficiency
            for i in range(0, len(filtered_results), batch_size):
                batch = filtered_results[i:i+batch_size]
                writer.writerows(batch)
                
        debug_print(f"Results saved as CSV: {filename}", "success", print_lock)
    
    elif output_format == "sqlite":
        filename = f"{save_dir}/{file_prefix}_{timestamp}.db"
        conn = sqlite3.connect(filename)
        conn.isolation_level = None  # Turn autocommit off for bulk inserts
        cursor = conn.cursor()
        
        try:
            # Create table
            cursor.execute('BEGIN TRANSACTION')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS proxies (
                proxy TEXT PRIMARY KEY,
                status TEXT,
                response_time REAL,
                country TEXT,
                city TEXT,
                anonymity TEXT,
                protocol TEXT,
                check_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Use executemany for batch processing
            batch_data = []
            for result in filtered_results:
                batch_data.append((
                    result["proxy"],
                    result["status"],
                    result["response_time"] if result["response_time"] != "N/A" else None,
                    result["country"],
                    result["city"],
                    result["anonymity"],
                    result["protocol"]
                ))
                
                # Process in batches
                if len(batch_data) >= batch_size:
                    cursor.executemany(
                        "INSERT OR REPLACE INTO proxies (proxy, status, response_time, country, city, anonymity, protocol) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        batch_data
                    )
                    batch_data = []
            
            # Insert any remaining data
            if batch_data:
                cursor.executemany(
                    "INSERT OR REPLACE INTO proxies (proxy, status, response_time, country, city, anonymity, protocol) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    batch_data
                )
            
            cursor.execute('COMMIT')
        except sqlite3.Error as e:
            cursor.execute('ROLLBACK')
            debug_print(f"SQLite error: {str(e)}", "error", print_lock)
        finally:
            conn.close()
            
        debug_print(f"Results saved as SQLite database: {filename}", "success", print_lock)
    
    # Also save a plain text file with just the working proxies
    working_proxies = [r["proxy"] for r in filtered_results if r["status"] in ["FAST", "SLOW"]]
    if working_proxies:
        txt_filename = f"{save_dir}/{file_prefix}_{timestamp}.txt"
        with open(txt_filename, "w") as f:
            # Use writelines for better performance with large lists
            f.writelines(f"{proxy}\n" for proxy in working_proxies)
        debug_print(f"Working proxies saved as TXT: {txt_filename}", "success", print_lock)

def signal_handler(sig, frame):
    """
    Handle interruption signals gracefully.
    
    Args:
        sig: Signal number
        frame: Current stack frame
    
    Returns:
        None
    """
    debug_print("\nInterrupted by user. Saving current results...", "warning", print_lock)
    
    # Try to save current results
    if global_results:
        config = load_config()
        autosave_results(global_results, config, in_progress=False)
        
    debug_print("Exiting gracefully.", "info", print_lock)
    
    # Clean up tasks to ensure proper shutdown
    cleanup_resources()
    sys.exit(0)
    
def cleanup_resources():
    """
    Clean up all resources before exiting.
    
    Returns:
        None
    """
    global http_session, aiohttp_session
    
    # Close HTTP session if it exists
    if http_session:
        try:
            http_session.close()
        except Exception:
            pass
    
    # Close aiohttp session if it exists
    if aiohttp_session and not aiohttp_session.closed:
        try:
            if sys.version_info >= (3, 7):
                # For Python 3.7+, we can use run() to close the session
                if asyncio.get_event_loop().is_running():
                    asyncio.create_task(aiohttp_session.close())
                else:
                    asyncio.run(aiohttp_session.close())
            else:
                # For earlier versions, we'll rely on garbage collection
                pass
        except Exception:
            pass

async def check_proxy_worker_async(proxy, test_url, timeout, response_time_filter, public_ip, anonymity_check_url, progress_info):
    """
    Asynchronous worker function to check a single proxy.
    
    Args:
        proxy (str): Proxy to check
        test_url (str): URL to test with
        timeout (int): Timeout in seconds
        response_time_filter (float): Filter for response time
        public_ip (str): Original public IP
        anonymity_check_url (str): URL for anonymity check
        progress_info (dict): Dictionary with progress information

    Returns:
        dict: Result of the proxy check
    """
    global global_results, results_counter, aiohttp_session, connection_semaphore
    
    # Update and get current progress
    with print_lock:
        progress_info['current'] += 1
        current_index = progress_info['current']
        total_proxies = progress_info['total']
    
    # Progress indicator
    progress = f"[{current_index}/{total_proxies}]"
    
    # Parse and detect proxy protocol
    parsed = urlparse(proxy)
    protocol = parsed.scheme.lower()
    host = parsed.hostname
    port = parsed.port or {'http': 80, 'https': 443, 'socks4': 1080, 'socks5': 1080}.get(protocol, 80)
    
    # Pre-resolve hostname to IP to reduce DNS lookup time
    ip_address = resolve_hostname(host)
    
    # Get geographical information for the proxy (asynchronously)
    country, city = await get_geoip_info_async(ip_address)
    
    # Check anonymity (asynchronously)
    detected_ip, anonymity = await check_anonymity_async(proxy, anonymity_check_url, public_ip)
    
    try:
        start_time = time.time()
        success = False
        connection_details = ""
        
        if protocol in ['http', 'https']:
            # Parse proxy for aiohttp format
            proxy_auth = ""
            if parsed.username and parsed.password:
                proxy_auth = f"{parsed.username}:{parsed.password}@"
            proxy_url = f"{parsed.scheme}://{proxy_auth}{parsed.hostname}:{parsed.port}"
            
            # Use semaphore to limit concurrent connections
            async with connection_semaphore:
                try:
                    async with aiohttp_session.get(test_url, proxy=proxy_url, timeout=timeout) as response:
                        success = response.status == 200
                        connection_details = f"HTTP {response.status}"
                except Exception as e:
                    success = False
                    connection_details = f"Error: {str(e)}"
                    
        elif protocol in ['socks4', 'socks5']:
            # For SOCKS proxies, use the async socket connection test
            parsed_test_url = urlparse(test_url)
            test_host = parsed_test_url.hostname
            test_port = parsed_test_url.port or (443 if parsed_test_url.scheme == 'https' else 80)
            
            success = await create_socket_connection_async(
                protocol, host, port, test_host, test_port, timeout
            )
            connection_details = "SOCKS connection successful" if success else "SOCKS connection failed"
        else:
            success = False
            connection_details = "Unsupported protocol"
        
        elapsed_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        if success:
            if response_time_filter and elapsed_time <= response_time_filter:
                debug_print(f"{progress} FAST - {proxy} ({country}, {city}, {anonymity}) - {elapsed_time:.0f} ms", "success", print_lock)
                status = "FAST"
            else:
                debug_print(f"{progress} SLOW - {proxy} ({country}, {city}, {anonymity}) - {elapsed_time:.0f} ms", "warning", print_lock)
                status = "SLOW"
        else:
            # Simplified error output in normal mode
            if global_args and global_args.debug:
                debug_print(f"{progress} FAILED - {proxy} ({country}, {city}, {anonymity}) - {connection_details}", "error", print_lock)
            else:
                debug_print(f"{progress} FAILED - {proxy}", "error", print_lock)
            status = "FAILED"
            elapsed_time = "N/A"
        
    except Exception as e:
        # Detailed error info only in debug mode
        if global_args and global_args.debug:
            debug_print(f"{progress} FAILED - {proxy} ({country}, {city}, {anonymity}) - {str(e)}", "error", print_lock)
        else:
            debug_print(f"{progress} FAILED - {proxy}", "error", print_lock)
        
        connection_details = f"Error: {type(e).__name__}"
        status = "FAILED"
        elapsed_time = "N/A"
    
    # Prepare the result
    result = {
        "proxy": proxy,
        "status": status,
        "response_time": elapsed_time if elapsed_time != "N/A" else "N/A",
        "country": country,
        "city": city,
        "anonymity": anonymity,
        "protocol": protocol,
        "check_time": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Add to global results
    with print_lock:
        global_results.append(result)
        results_counter += 1
        
        # Autosave every N proxies, using the configured frequency
        config = load_config()
        autosave_frequency = int(config.get('advanced', 'autosave_batch', fallback=AUTOSAVE_FREQUENCY))
        if results_counter % autosave_frequency == 0:
            autosave_results(global_results, config)
    
    return result

async def process_proxies_async(proxies, test_url, timeout, response_time_filter, public_ip, anonymity_check_url, thread_count):
    """
    Process proxies using asynchronous workers for maximum performance.
    
    Args:
        proxies (list): List of proxies to check
        test_url (str): URL to test with
        timeout (int): Timeout in seconds
        response_time_filter (float): Filter for response time
        public_ip (str): Original public IP address
        anonymity_check_url (str): URL to check anonymity
        thread_count (int): Maximum number of concurrent tasks
        
    Returns:
        list: Results of proxy checks
    """
    global aiohttp_session, connection_semaphore
    
    # Initialize aiohttp session
    connector = aiohttp.TCPConnector(limit=thread_count, ttl_dns_cache=300)
    aiohttp_session = aiohttp.ClientSession(connector=connector)
    
    # Initialize semaphore
    connection_semaphore = asyncio.Semaphore(thread_count)
    
    try:
        debug_print(f"Starting async proxy checks with {thread_count} concurrent connections", "info", print_lock)
        
        # Initialize progress tracking
        progress_info = {
            'current': 0,
            'total': len(proxies)
        }
        
        # Process proxies in chunks to avoid memory issues with very large lists
        chunk_size = min(1000, len(proxies))
        results = []
        
        for i in range(0, len(proxies), chunk_size):
            chunk = proxies[i:i+chunk_size]
            debug_print(f"Processing chunk {i//chunk_size + 1}/{(len(proxies) + chunk_size - 1)//chunk_size}", "info", print_lock)
            
            # Create tasks for all proxies in the chunk
            tasks = []
            for proxy in chunk:
                task = asyncio.create_task(check_proxy_worker_async(
                    proxy, test_url, timeout, response_time_filter, 
                    public_ip, anonymity_check_url, progress_info
                ))
                tasks.append(task)
            
            # Wait for all tasks in the chunk to complete
            chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and add valid results
            for result in chunk_results:
                if not isinstance(result, Exception) and result is not None:
                    results.append(result)
                    
        return results
    finally:
        # Stellen Sie sicher, dass die Session geschlossen wird
        if aiohttp_session and not aiohttp_session.closed:
            await aiohttp_session.close()
            

def batch_process_proxies(proxies, test_url, timeout, response_time_filter, public_ip, anonymity_check_url, thread_count):
    """
    Process proxies in batches using ThreadPoolExecutor.
    
    Args:
        proxies (list): List of proxies to check
        test_url (str): URL to test with
        timeout (int): Timeout in seconds
        response_time_filter (float): Filter for response time
        public_ip (str): Original public IP address
        anonymity_check_url (str): URL to check anonymity
        thread_count (int): Maximum number of concurrent threads
        
    Returns:
        list: Results of proxy checks
    """
    debug_print(f"Starting proxy checks with {thread_count} concurrent workers in batch mode", "info", print_lock)
    
    # Initialize progress tracking
    progress_info = {
        'current': 0,
        'total': len(proxies)
    }
    
    # Process proxies in chunks to avoid memory issues with very large lists
    chunk_size = min(5000, len(proxies))
    all_results = []
    
    for i in range(0, len(proxies), chunk_size):
        chunk = proxies[i:i+chunk_size]
        debug_print(f"Processing chunk {i//chunk_size + 1}/{(len(proxies) + chunk_size - 1)//chunk_size}", "info", print_lock)
        
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            # Submit all proxy checks in this chunk to the executor
            future_to_proxy = {
                executor.submit(
                    check_proxy_worker,
                    proxy,
                    test_url,
                    timeout,
                    response_time_filter,
                    public_ip,
                    anonymity_check_url,
                    progress_info
                ): proxy for proxy in chunk
            }
            
            # As each future completes
            for future in concurrent.futures.as_completed(future_to_proxy):
                try:
                    # Retrieve the result (but we already saved it in the worker)
                    result = future.result()
                    if result:
                        all_results.append(result)
                except Exception as e:
                    if global_args.debug:
                        debug_print(f"Error processing proxy: {str(e)}", "error", print_lock)
    
    return all_results

def main():
    """
    Main entry point of the script.
    """
    global global_args, global_results, http_session, aiohttp_session

    # Register signal handler for graceful exit
    signal.signal(signal.SIGINT, signal_handler)

    # clear screen
    clear_screen()

    # Always display the banner at startup
    display_banner()
    print("\n")  # Add 2 lines of spacing

    # Load configuration
    config = load_config()

    # Parse command line arguments
    parser = argparse.ArgumentParser(description=f'{APP_NAME} - Check proxies for availability, speed, and anonymity')
    parser.add_argument('url', nargs='?', help='URL to test')
    parser.add_argument('-p', '--proxy', type=str, help='Proxy or file with proxies (comma-separated or .txt file)')
    parser.add_argument('-t', '--timeout', type=int, help='Timeout in seconds (default from config)')
    parser.add_argument('-o', '--output', type=str, choices=["json", "csv", "sqlite"], help='Save results format')
    parser.add_argument('-R', '--response-time', type=float, help='Filter for fast proxies (maximum response time in ms)')
    parser.add_argument('-v', '--version', action='store_true', help='Display version information and exit')
    parser.add_argument('-f', '--fast-only', action='store_true', help='Save only fast proxies to the output file')
    parser.add_argument('-c', '--concurrent', type=int, help='Number of concurrent checks')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable detailed debug output')
    parser.add_argument('-A', '--automatic-mode', action='store_true', help='Download proxy lists from configured URLs')
    parser.add_argument('--config', action='store_true', help='Create default config file in ~/.proxyreaper.conf')
    parser.add_argument('--async', action='store_true', help='Use asynchronous processing for improved performance')
    parser.add_argument('--batch-size', type=int, help='Batch size for processing large proxy lists')

    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()
    global_args = args  # Make args globally accessible

    # Create default config if requested
    if args.config:
        user_config = os.path.expanduser('~/.proxyreaper.conf')
        if create_default_config(user_config):
            debug_print(f"Created default configuration file at {user_config}", "success")
        else:
            debug_print(f"Failed to create configuration file", "error")
        sys.exit(0)

    # Show version and exit if requested
    if args.version:
        sys.exit(0)

    # Override config with command line arguments
    config = override_config_with_args(config, args)

    # Extract key parameters from config
    timeout = int(config.get('general', 'timeout'))
    thread_count = int(config.get('general', 'concurrent'))
    response_time_filter = float(config.get('general', 'response_time_filter')) if config.get('general', 'response_time_filter') else None
    test_url = config.get('general', 'test_url') or "https://www.google.com"
    output_format = config.get('output', 'format')
    fast_only = config.getboolean('output', 'fast_only')
    anonymity_check_url = config.get('advanced', 'anonymity_check_url')
    use_async = config.getboolean('advanced', 'use_async')
    chunk_size = int(config.get('general', 'chunk_size'))

    # Override with command line arguments if provided
    if args.url:
        test_url = args.url
    if args.timeout:
        timeout = args.timeout
    if args.concurrent:
        thread_count = args.concurrent
    if args.response_time is not None:
        response_time_filter = args.response_time
    if args.output:
        output_format = args.output
    if args.fast_only:
        fast_only = True
    if getattr(args, 'async', False):  # Use getattr because 'async' is a keyword
        use_async = True
    if args.batch_size:
        chunk_size = args.batch_size
        
# Initialize HTTP sessions with the specified concurrent limit
    initialize_sessions(thread_count)

    # Get the public IP address for anonymity checks
    debug_print("Determining your public IP address...", "info", print_lock)
    
    # Choose between sync and async methods based on configuration
    if use_async:
        # Für async IP lookup, neuerer Ansatz für Python 3.10+
        if hasattr(asyncio, 'run'):
            public_ip = asyncio.run(get_public_ip_async())
        else:
            # Fallback für ältere Python-Versionen
            loop = asyncio.get_event_loop()
            public_ip = loop.run_until_complete(get_public_ip_async())
    else:
        public_ip = get_public_ip()
    
    debug_print(f"Your public IP: {public_ip}", "info", print_lock)

    # Parse the proxies input
    debug_print("Parsing proxies from input...", "info", print_lock)
    if args.automatic_mode:
        proxies = parse_proxies(args.proxy, auto_mode=True)
    elif args.proxy:
        proxies = parse_proxies(args.proxy)
    else:
        debug_print("Error: No proxy source specified. Use -p/--proxy or -A/--automatic-mode", "error", print_lock)
        sys.exit(1)

    total_proxies = len(proxies)

    if total_proxies == 0:
        debug_print("No valid proxies found. Exiting.", "error", print_lock)
        sys.exit(1)

    debug_print(f"Testing {total_proxies} proxies with a timeout of {timeout} seconds", "info", print_lock)
    if global_args.debug:
        debug_print("Debug mode enabled - showing detailed information", "debug", print_lock)
    
    
    # Process the proxies using either asynchronous or batch mode
    start_time = time.time()
    
    if use_async:
        debug_print(f"Using asynchronous processing mode with {thread_count} concurrent connections", "info", print_lock)
        
        # Initialize asyncio loop and run the async processing function
        try:
            # Neuerer Ansatz, der mit Python 3.10+ kompatibel ist
            if hasattr(asyncio, 'run'):
                # Python 3.7+ nutzt asyncio.run
                asyncio.run(
                    process_proxies_async(
                        proxies, test_url, timeout, response_time_filter,
                        public_ip, anonymity_check_url, thread_count
                    )
                )
            else:
                # Fallback für ältere Python-Versionen
                loop = asyncio.get_event_loop()
                loop.run_until_complete(
                    process_proxies_async(
                        proxies, test_url, timeout, response_time_filter,
                        public_ip, anonymity_check_url, thread_count
                    )
                )
        except Exception as e:
            debug_print(f"Error in async processing: {str(e)}", "error", print_lock)
        finally:
            # Cleanup async resources
            if aiohttp_session and not aiohttp_session.closed:
                if hasattr(asyncio, 'run'):
                    asyncio.run(aiohttp_session.close())
                else:
                    loop = asyncio.get_event_loop()
                    loop.run_until_complete(aiohttp_session.close())
    
    else:
        debug_print(f"Using batch processing mode with {thread_count} concurrent threads", "info", print_lock)
        # Use the optimized batch processing function
        batch_process_proxies(
            proxies, test_url, timeout, response_time_filter,
            public_ip, anonymity_check_url, thread_count
        )
    
    # Calculate and display processing time
    total_time = time.time() - start_time
    proxies_per_second = total_proxies / total_time if total_time > 0 else 0
    debug_print(f"\nProcessed {total_proxies} proxies in {total_time:.2f} seconds ({proxies_per_second:.2f} proxies/second)", 
                "success", print_lock)

    # Save final results
    debug_print("\nAll proxy checks completed!", "success", print_lock)
    if output_format:
        debug_print("Saving final results...", "info", print_lock)
        save_results(global_results, output_format, fast_only, config)

    # Save final autosave
    autosave_results(global_results, config, in_progress=False)

    # Print summary
    working_proxies = sum(1 for r in global_results if r["status"] in ["FAST", "SLOW"])
    fast_proxies = sum(1 for r in global_results if r["status"] == "FAST")
    high_anon = sum(1 for r in global_results if r["anonymity"] == "High Anonymous" and r["status"] in ["FAST", "SLOW"])

    debug_print("\n─────────────────────────────", "info", print_lock)
    debug_print(" PROXY REAPER SUMMARY", "success", print_lock)
    debug_print("─────────────────────────────", "info", print_lock)
    debug_print(f"Total proxies tested: {total_proxies}", "info", print_lock)
    debug_print(f"Working proxies: {working_proxies} ({(working_proxies/total_proxies*100):.1f}%)", "success", print_lock)
    debug_print(f"Fast proxies: {fast_proxies} ({(fast_proxies/total_proxies*100):.1f}%)", "success", print_lock)
    debug_print(f"High anonymous proxies: {high_anon} ({(high_anon/total_proxies*100):.1f}%)", "high_anonymous", print_lock)
    debug_print(f"Processing speed: {proxies_per_second:.2f} proxies/second", "info", print_lock)
    debug_print("─────────────────────────────", "info", print_lock)
    
    # Clean up resources
    cleanup_resources()

# Entry point
if __name__ == '__main__':
    main()
