#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proxy Reaper

This script checks a list of proxies for availability, speed, and anonymity.
It supports various protocols such as HTTP, HTTPS, SOCKS4, and SOCKS5.
Results can be saved as JSON or CSV, and fast proxies can be filtered and saved in a separate file.

Author: Robert Tulke
License: MIT
"""

# Application configuration
APP_NAME = "Proxy Reaper"
VERSION = "1.3.2"

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
from urllib.parse import urlparse
from colorama import init as colorama_init, Fore, Back, Style

# Initialize Colorama for ANSI color support (also on Windows)
colorama_init(autoreset=True)

# Global print lock to avoid garbled output from multiple threads
print_lock = threading.Lock()

# Global args variable to make debug flag accessible
global_args = None

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

def debug_print(message, level="info", lock=None):
    """
    Print messages with different colors based on level and respect debug flag.
    Levels: info, success, warning, error, debug
    """
    if level == "debug" and (global_args is None or not global_args.debug):
        return
        
    colors = {
        "info": Fore.CYAN,
        "success": Fore.GREEN,
        "warning": Fore.YELLOW,
        "error": Fore.RED,
        "debug": Fore.MAGENTA
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
        print(padding + Fore.BLUE + Style.BRIGHT + version_str + Style.RESET_ALL, flush=True)

def get_public_ip():
    """Determines the user's actual public IP address using fallback services."""
    services = [
        'https://api64.ipify.org?format=json',
        'https://ipinfo.io/json',
        'https://api.my-ip.io/ip.json',
        'https://api.ipify.org?format=json'  # Added another fallback service
    ]
    for service in services:
        try:
            response = requests.get(service, timeout=5)
            if response.status_code == 200:
                data = response.json()
                for key in ["ip", "ip_addr", "origin"]:  # Added "origin" as a possible key
                    ip = data.get(key)
                    if ip:
                        return ip
        except (requests.RequestException, json.JSONDecodeError) as e:
            debug_print(f"Failed to get IP from {service}: {str(e)}", "debug", print_lock)
            continue
    return "Unknown"

def parse_proxies(proxy_input):
    """Parse proxy input which can be a single proxy, a comma-separated list, or a file path."""
    proxies = []
    if ',' in proxy_input:
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
    
    # Validate proxies format
    valid_proxies = []
    for proxy in proxies:
        # Normalize proxy format
        if '://' not in proxy:
            # No protocol specified, assume it's a host:port
            if ':' in proxy:
                valid_proxies.append(proxy)
            else:
                debug_print(f"Warning: Skipping invalid proxy format: {proxy}", "warning", print_lock)
        else:
            # Protocol specified
            valid_proxies.append(proxy)
    
    debug_print(f"Validated {len(valid_proxies)} proxies", "debug", print_lock)
    return valid_proxies

def sanitize_proxy(proxy):
    """Remove any unsafe characters from proxy string."""
    return re.sub(r'[^a-zA-Z0-9.:@/_-]', '', proxy)

def get_geoip_info(ip):
    """Get geographical information about an IP address."""
    services = [
        {'url': f'https://ipinfo.io/{ip}/json', 'country_key': 'country', 'city_key': 'city'},
        {'url': f'https://freegeoip.app/json/{ip}', 'country_key': 'country_name', 'city_key': 'city'},
        {'url': f'https://ipapi.co/{ip}/json/', 'country_key': 'country_name', 'city_key': 'city'}
    ]
    
    for service in services:
        try:
            response = requests.get(service['url'], timeout=5)
            if response.status_code == 200:
                data = response.json()
                country = data.get(service['country_key'], "Unknown")
                city = data.get(service['city_key'], "Unknown")
                debug_print(f"Got geo info for {ip}: {country}, {city}", "debug", print_lock)
                return country, city
        except (requests.RequestException, json.JSONDecodeError) as e:
            debug_print(f"Failed to get geo info from {service['url']}: {str(e)}", "debug", print_lock)
            continue
    
    return "Unknown", "Unknown"

def check_anonymity(proxy, anonymity_check_url, original_ip):
    """
    Checks if a proxy hides the IP address and evaluates additional headers.
    It uses a dedicated URL (e.g. https://httpbin.org/get) which returns the incoming headers.
    
    Returns:
        tuple: (detected_ip, anonymity_level)
    """
    try:
        debug_print(f"Checking anonymity for {proxy}", "debug", print_lock)
        response = requests.get(anonymity_check_url, proxies={"http": proxy, "https": proxy}, timeout=5)
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
        
        # Check for header leaks that might reveal original IP
        for header in ["x-forwarded-for", "via", "forwarded", "client-ip"]:
            if header in headers_info:
                value = headers_info[header]
                if original_ip in value:
                    debug_print(f"Transparent proxy detected - original IP leaked in {header} header", "debug", print_lock)
                    return proxy_ip, "Transparent"
        
        # Check if proxy reveals itself as a proxy via headers
        for header in ["via", "proxy-connection"]:
            if header in headers_info:
                debug_print(f"Proxy reveals itself via {header} header", "debug", print_lock)
                return proxy_ip, "Anonymous (Header leak)"
        
        if proxy_ip != original_ip:
            debug_print(f"Anonymous proxy detected: {proxy_ip}", "debug", print_lock)
            return proxy_ip, "Anonymous"
        else:
            debug_print(f"Transparent proxy detected: {proxy_ip}", "debug", print_lock)
            return proxy_ip, "Transparent"
    
    except requests.RequestException as e:
        debug_print(f"Anonymity check exception: {str(e)}", "debug", print_lock)
        return "Unknown", "Failed"

def create_socket_connection(proxy_type, proxy_host, proxy_port, target_host, target_port, timeout):
    """
    Create a SOCKS connection to test SOCKS4/SOCKS5 proxies.
    
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

def save_results(results, output_format, filter_fast=False):
    """Save results to a file in the specified format."""
    if not results:
        debug_print("No results available to save.", "error", print_lock)
        return
    
    # Create results directory if it doesn't exist
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # Filter fast proxies if requested
    if filter_fast:
        filtered_results = [r for r in results if r["status"] == "FAST"]
        file_prefix = "fast_proxies"
    else:
        filtered_results = results
        file_prefix = "proxy_results"
    
    debug_print(f"Saving {len(filtered_results)} results", "debug", print_lock)
    
    if output_format == "json":
        filename = f"{results_dir}/{file_prefix}_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(filtered_results, f, indent=4)
        debug_print(f"Results saved as JSON: {filename}", "success", print_lock)
    
    elif output_format == "csv":
        filename = f"{results_dir}/{file_prefix}_{timestamp}.csv"
        with open(filename, "w", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["proxy", "status", "response_time", "country", "city", "anonymity", "protocol"])
            writer.writeheader()
            writer.writerows(filtered_results)
        debug_print(f"Results saved as CSV: {filename}", "success", print_lock)
    
    # Also save a plain text file with just the working proxies
    if filter_fast or not filter_fast:
        working_proxies = [r["proxy"] for r in filtered_results if r["status"] in ["FAST", "SLOW"]]
        if working_proxies:
            txt_filename = f"{results_dir}/{file_prefix}_{timestamp}.txt"
            with open(txt_filename, "w") as f:
                for proxy in working_proxies:
                    f.write(f"{proxy}\n")
            debug_print(f"Working proxies saved as TXT: {txt_filename}", "success", print_lock)

def detect_proxy_protocol(proxy):
    """
    Detect the protocol of a proxy from its string representation.
    Returns a tuple of (full_proxy_url, protocol, host, port).
    """
    debug_print(f"Detecting protocol for proxy: {proxy}", "debug", print_lock)
    if '://' in proxy:
        parsed = urlparse(proxy)
        protocol = parsed.scheme.lower()
        host = parsed.hostname
        port = parsed.port or {'http': 80, 'https': 443, 'socks4': 1080, 'socks5': 1080}.get(protocol, 80)
        username = parsed.username
        password = parsed.password
        
        # Rebuild the proxy URL with proper format
        auth_part = f"{username}:{password}@" if username and password else ""
        full_proxy = f"{protocol}://{auth_part}{host}:{port}"
        
        debug_print(f"Parsed proxy with protocol: {protocol}://{host}:{port}", "debug", print_lock)
        return full_proxy, protocol, host, port
    else:
        # No protocol specified, try to parse as host:port
        parts = proxy.split(':')
        if len(parts) == 2:
            host, port = parts
            # Default to HTTP protocol
            protocol = 'http'
            debug_print(f"Proxy without protocol, using default HTTP: {host}:{port}", "debug", print_lock)
            return f"http://{host}:{port}", protocol, host, port
        else:
            # Invalid format
            debug_print(f"Invalid proxy format: {proxy}", "debug", print_lock)
            return None, None, None, None

def check_proxy(proxy, test_url, timeout, response_time_filter, public_ip, results, stop_event, total_proxies, current_index):
    """Check a proxy for availability, speed, and anonymity."""
    if stop_event.is_set():
        return
    
    # Progress indicator
    progress = f"[{current_index}/{total_proxies}]"
    
    # Parse and detect proxy protocol
    full_proxy, protocol, host, port = detect_proxy_protocol(proxy)
    if not full_proxy:
        debug_print(f"{progress} Invalid proxy format: {proxy}", "error", print_lock)
        return
    
    # Get geographical information for the proxy
    country, city = get_geoip_info(host)
    
    # Set up proxy dictionary for requests
    proxy_dict = {
        "http": full_proxy,
        "https": full_proxy
    }
    
    # Check anonymity
    detected_ip, anonymity = check_anonymity(full_proxy, 'https://httpbin.org/get', public_ip)
    
    try:
        start_time = time.time()
        
        # Handle different proxy protocols
        if protocol in ['http', 'https']:
            response = requests.get(test_url, proxies=proxy_dict, timeout=timeout)
            success = response.status_code == 200
        elif protocol in ['socks4', 'socks5']:
            # For SOCKS proxies, we need to test differently
            parsed_test_url = urlparse(test_url)
            test_host = parsed_test_url.hostname
            test_port = parsed_test_url.port or (443 if parsed_test_url.scheme == 'https' else 80)
            success = create_socket_connection(protocol, host, port, test_host, test_port, timeout)
        else:
            success = False
        
        elapsed_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        if success:
            if response_time_filter and elapsed_time <= response_time_filter:
                # Only show detailed info in regular mode for successful proxies
                debug_print(f"{progress} FAST - {full_proxy} ({country}, {city}, {anonymity}) - {elapsed_time:.0f} ms", "success", print_lock)
                status = "FAST"
            else:
                debug_print(f"{progress} SLOW - {full_proxy} ({country}, {city}, {anonymity}) - {elapsed_time:.0f} ms", "warning", print_lock)
                status = "SLOW"
        else:
            # Simplified error output in normal mode
            if global_args and global_args.debug:
                debug_print(f"{progress} FAILED - {full_proxy} ({country}, {city}, {anonymity}) - Connection failed", "error", print_lock)
            else:
                debug_print(f"{progress} FAILED - {full_proxy}", "error", print_lock)
            status = "FAILED"
            elapsed_time = "N/A"
        
    except requests.RequestException as e:
        # Detailed error info only in debug mode
        if global_args and global_args.debug:
            debug_print(f"{progress} FAILED - {full_proxy} ({country}, {city}, {anonymity}) - {str(e)}", "error", print_lock)
        else:
            debug_print(f"{progress} FAILED - {full_proxy}", "error", print_lock)
        
        # Additional debug information about the exception
        debug_print(f"{progress} Exception details: {type(e).__name__}: {str(e)}", "debug", print_lock)
        
        status = "FAILED"
        elapsed_time = "N/A"
    
    # Add result to the results list
    result = {
        "proxy": sanitize_proxy(full_proxy),
        "status": status,
        "response_time": elapsed_time if elapsed_time != "N/A" else "N/A",
        "country": country,
        "city": city,
        "anonymity": anonymity,
        "protocol": protocol
    }
    
    results.append(result)

def signal_handler(sig, frame):
    """Handle CTRL+C interruptions gracefully."""
    debug_print("\nUser interruption detected. Saving results and exiting the program...", "error", print_lock)
    # You could save the current results here if needed
    sys.exit(0)

def main():
    global global_args
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Always display the banner at startup
    display_banner()
    print("\n")  # Add 2 lines of spacing
    
    parser = argparse.ArgumentParser(description=f'{APP_NAME} - Check proxies for availability, speed, and anonymity')
    parser.add_argument('url', nargs='?', default=None, help='URL to test')
    parser.add_argument('-p', '--proxy', type=str, help='Proxy or file with proxies (comma-separated or .txt file)')
    parser.add_argument('-t', '--timeout', type=int, default=5, help='Timeout in seconds (default: 5)')
    parser.add_argument('-o', '--output', type=str, choices=["json", "csv"], help='Save results as JSON or CSV')
    parser.add_argument('-R', '--response-time', type=float, help='Filter for fast proxies (maximum response time in milliseconds)')
    parser.add_argument('-v', '--version', action='store_true', help='Display version information and exit')
    parser.add_argument('-f', '--fast-only', action='store_true', help='Save only fast proxies to the output file')
    parser.add_argument('-c', '--concurrent', type=int, default=10, help='Number of concurrent checks (default: 10)')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable detailed debug output')
    
    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    
    args = parser.parse_args()
    global_args = args  # Make args globally accessible
    
    # Show version and exit if requested
    if args.version:
        sys.exit(0)
    
    # Check if required arguments are provided
    if args.url is None or args.proxy is None:
        debug_print("Error: URL and proxy are required unless using the -b/--banner or -v/--version flags.", "error", print_lock)
        sys.exit(1)
    
    # Get the public IP address for anonymity checks
    debug_print("Determining your public IP address...", "info", print_lock)
    public_ip = get_public_ip()
    debug_print(f"Your public IP: {public_ip}", "info", print_lock)
    
    # Parse the proxies input
    debug_print("Parsing proxies from input...", "info", print_lock)
    proxies = parse_proxies(args.proxy)
    total_proxies = len(proxies)
    
    if total_proxies == 0:
        debug_print("No valid proxies found. Exiting.", "error", print_lock)
        sys.exit(1)
    
    debug_print(f"Testing {total_proxies} proxies with a timeout of {args.timeout} seconds", "info", print_lock)
    if args.debug:
        debug_print("Debug mode enabled - showing detailed information", "debug", print_lock)
    
    # Initialize results list and threading control
    results = []
    stop_event = threading.Event()
    
    # Use semaphore to limit concurrent threads
    semaphore = threading.Semaphore(args.concurrent)
    
    # Create and start threads for proxy checking
    threads = []
    for i, proxy in enumerate(proxies, 1):
        # Use semaphore to control concurrency
        semaphore.acquire()
        
        thread = threading.Thread(
            target=lambda p=proxy, idx=i: [
                check_proxy(p, args.url, args.timeout, args.response_time, public_ip, results, stop_event, total_proxies, idx),
                semaphore.release()  # Release the semaphore when done
            ]
        )
        thread.daemon = True
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to finish
    for thread in threads:
        thread.join()
    
    # Save results if output format is specified
    if args.output:
        debug_print("Saving results...", "info", print_lock)
        save_results(results, args.output, args.fast_only)
    
    # Print summary
    working_proxies = sum(1 for r in results if r["status"] in ["FAST", "SLOW"])
    fast_proxies = sum(1 for r in results if r["status"] == "FAST")
    
    debug_print("\n─────────────────────────────", "info", print_lock)
    debug_print(" PROXY REAPER SUMMARY", "success", print_lock)
    debug_print("─────────────────────────────", "info", print_lock)
    debug_print(f"Total proxies tested: {total_proxies}", "info", print_lock)
    debug_print(f"Working proxies: {working_proxies} ({(working_proxies/total_proxies*100):.1f}%)", "success", print_lock)
    debug_print(f"Fast proxies: {fast_proxies} ({(fast_proxies/total_proxies*100):.1f}%)", "success", print_lock)
    debug_print("─────────────────────────────", "info", print_lock)

if __name__ == '__main__':
    main()
