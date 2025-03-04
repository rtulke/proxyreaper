## Proxy Reaper - Documentation

![Proxy Reaper Banner](https://raw.githubusercontent.com/rtulke/proxyreaper/main/demo/proxyreaper.gif)

Proxy Reaper is a powerful tool for checking proxy servers for availability, speed and anonymity. It supports various protocols such as HTTP, HTTPS, SOCKS4, and SOCKS5, and offers enhanced features for managing and testing proxies efficiently.

## Table of Contents

1. [Installation](#installation)
2. [Installing OS wide (Debian based Distributions)](#Installing-OS-wide)
3. [Basic Usage](#basic-usage)
4. [Command Line Arguments](#command-line-arguments)
5. [Configuration File](#configuration-file)
6. [Proxy Formats and Sources](#proxy-formats-and-sources)
7. [Anonymity Levels](#anonymity-levels)
8. [Output Formats](#output-formats)
9. [Advanced Features](#advanced-features)
10. [Troubleshooting](#troubleshooting)
11. [Examples](#examples)

## Installation

### Prerequisites

- Python 3.6 or higher
- Required Python packages:
  - requests
  - PySocks
  - colorama


### Download and Installation

```bash
# Clone the repository (if using Git)
git clone https://github.com/rtulke/proxyreaper.git
cd proxyreaper

# Or download the script directly
wget https://raw.githubusercontent.com/rtulke/proxyreaper/main/proxyreaper.py
chmod +x proxyreaper.py
```


### Installing Dependencies


```bash
pip install requests PySocks colorama
```

or use the requirements.txt file:

#### Linux / MacOS
```bash
cd proxyreaper
chmod +x proxyreaper.py
python -m venv venv
source source venv/bin/activate
pip install -r requirements.txt
```

#### Windows 

```bash
cd proxyreaper 
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Installing OS wide
The system wide installation works for the most Debian based Distributions, like Debian, Ubuntu, Mint, Raspberry PI OS, Kali Linux...

```bash
# start as root or try: "sudo su -" or "sudo -i"
su - root
sudo cd ~

# create dev directory for development stuff if needed
sudo mkdir dev
sudo cd dev

# download via git
sudo git clone https://github.com/rtulke/proxyreaper.git
sudo cd proxyreaper
sudo chmod +x proxyreaper.py

# install dependecies
sudo apt install python3-socks python3-colorama

# copy proxyreaper script to `/usr/local/bin`
sudo cp proxyreaper.py /usr/local/bin/proxyrepaer

# install man page and updating mandb
sudo cp proxyreaper.1 /usr/local/share/man/man1/
sudo mandb

# use the proxyreaper script from any directory
$ proxyreaper -h

# generate new config file
$ proxyreaper --config

# you can also try to edit the configuration file
$ vim ~/.proxyreaper.conf

# try using the manual
$ man proxyreaper
```


## Basic Usage

```bash
# Test a single proxy
python proxyreaper.py https://www.google.com -p 1.2.3.4:8080

# Test multiple proxies from a file
python proxyreaper.py https://www.google.com -p proxies.txt

# Create a default configuration file
python proxyreaper.py --config

# Use automatic mode to download proxies from URLs defined in the config, in the part `[proxysources]`
python proxyreaper.py https://www.google.com -A
```

## Command Line Arguments

| Argument | Description |
|----------|-------------|
| `url` | URL to test the proxies against |
| `-p, --proxy` | Proxy or file with proxies (comma-separated or .txt file) |
| `-t, --timeout` | Timeout in seconds (default from config) |
| `-o, --output` | Save results format (json, csv, txt, or sqlite) |
| `-R, --response-time` | Filter for fast proxies (maximum response time in milliseconds) |
| `-v, --version` | Display version information and exit |
| `-f, --fast-only` | Save only fast proxies to the output file |
| `-c, --concurrent` | Number of concurrent checks |
| `-d, --debug` | Enable detailed debug output |
| `-A, --automatic-mode` | Download proxy lists from configured URLs |
| `--config` | Create default config file in ~/.proxyreaper.conf |

## Configuration File

Proxy Reaper supports configuration files to store frequently used settings. The configuration files are searched in the following order:

1. `~/.proxyreaper.conf` (user-specific configuration)
2. `/etc/proxyreaper.conf` (system-wide configuration)
3. Default values (if no configuration file is found)

### Creating a Configuration File

You can create a default configuration file using:

```bash
python proxyreaper.py --config
```

This will create a file at `~/.proxyreaper.conf` with default values.

### Configuration File Format

The configuration file uses the INI format with the following sections:

```ini
[general]
timeout = 5
concurrent = 10
response_time_filter = 1000
test_url = https://www.google.com

[output]
format = json
fast_only = false
save_directory = results

[proxysources]
urls = https://raw.githubusercontent.com/username/proxy-list/main/proxies.txt, https://some-proxy-list.com/proxies.txt

[advanced]
debug = false
anonymity_check_url = https://httpbin.org/get
```

### Configuration Sections Explained

#### [general]

- `timeout`: Connection timeout in seconds (default: 5)
- `concurrent`: Number of concurrent proxy checks (default: 10)
- `response_time_filter`: Maximum response time in milliseconds for "FAST" proxies (default: 1000)
- `test_url`: URL to use for testing proxies (default: https://www.google.com)

#### [output]

- `format`: Default output format (json, csv, or sqlite)
- `fast_only`: Whether to only save fast proxies by default (true/false)
- `save_directory`: Directory to save results (default: results)

#### [proxysources]

- `urls`: Comma-separated list of URLs to download proxy lists from when using automatic mode

#### [advanced]

- `debug`: Enable detailed debug output by default (true/false)
- `anonymity_check_url`: URL to use for anonymity checks (default: https://httpbin.org/get)

## Proxy Formats and Sources

### Supported Proxy Formats

Proxy Reaper supports several proxy formats:

- `host:port` (e.g., `127.0.0.1:8080`) - Defaults to HTTP protocol
- `protocol://host:port` (e.g., `http://127.0.0.1:8080`)
- `protocol://username:password@host:port` (e.g., `http://user:pass@127.0.0.1:8080`)

Supported protocols:
- HTTP
- HTTPS
- SOCKS4
- SOCKS5

### Proxy Input Methods

1. **Single Proxy**: Directly specify a proxy on the command line
   ```bash
   python proxyreaper.py https://www.google.com -p 127.0.0.1:8080
   ```

2. **Multiple Proxies**: Use comma-separated list
   ```bash
   python proxyreaper.py https://www.google.com -p "127.0.0.1:8080,192.168.1.1:3128"
   ```

3. **Text File**: Provide a file with one proxy per line
   ```bash
   python proxyreaper.py https://www.google.com -p proxies.txt
   ```

4. **Automatic Download**: Use the automatic mode to download proxies from URLs specified in the configuration
   ```bash
   python proxyreaper.py https://www.google.com -A
   ```

### Example Proxy List File

A proxy list file (e.g., `proxies.txt`) should contain one proxy per line:

```
# HTTP proxies
http://192.168.1.1:8080
http://user:pass@192.168.1.2:8080

# HTTPS proxies
https://192.168.1.3:443

# SOCKS proxies
socks4://192.168.1.4:1080
socks5://192.168.1.5:1080

# Without protocol (defaults to HTTP)
192.168.1.6:8080
```

Lines starting with `#` are treated as comments and ignored.

## Anonymity Levels

Proxy Reaper categorizes proxies into different anonymity levels and uses color coding for easy identification:

| Level | Color | Description |
|-------|-------|-------------|
| **High Anonymous** | Green (Bright) | Your IP address and proxy status are completely hidden |
| **Anonymous** | Blue (Bright) | Your IP address is hidden, but the server knows you're using a proxy |
| **Anonymous (Header leak)** | Yellow | Your IP is hidden, but proxy headers are visible |
| **Transparent** | Red | Your original IP address is visible to the server |

### How Anonymity is Determined

1. **High Anonymous**: The proxy changes your IP and doesn't add proxy-related headers
2. **Anonymous (Header leak)**: The proxy changes your IP but adds headers that reveal it's a proxy
3. **Transparent**: The proxy doesn't hide your original IP address or adds it to request headers

## Output Formats

Proxy Reaper supports multiple output formats:

### JSON Output

```bash
python proxyreaper.py https://www.google.com -p proxies.txt -o json
```

Creates a JSON file with detailed proxy information:

```json
[
  {
    "proxy": "http://192.168.1.1:8080",
    "status": "FAST",
    "response_time": 345.67,
    "country": "United States",
    "city": "New York",
    "anonymity": "High Anonymous",
    "protocol": "http",
    "check_time": "2023-10-01 15:30:45"
  },
  ...
]
```

### CSV Output

```bash
python proxyreaper.py https://www.google.com -p proxies.txt -o csv
```

Creates a CSV file with the same information in tabular format:

```
proxy,status,response_time,country,city,anonymity,protocol
http://192.168.1.1:8080,FAST,345.67,United States,New York,High Anonymous,http
...
```

### SQLite Output

```bash
python proxyreaper.py https://www.google.com -p proxies.txt -o sqlite
```

Creates an SQLite database with a `proxies` table containing the proxy information. This is useful for more complex queries and data analysis.

### Text Output

In addition to the specified format, Proxy Reaper always creates a plain text file with just the working proxies (one per line), which can be easily used in other applications.

## Advanced Features

### Automatic Saving During Execution

Proxy Reaper automatically saves intermediate results every 5 proxies checked. This ensures that even if the program is interrupted, you won't lose your progress. These autosaves are stored in the `results` directory with a timestamp and the `_partial` suffix.

### GeoIP Caching

To improve performance and reduce API calls, Proxy Reaper caches geographical information for IP addresses. This significantly speeds up testing when multiple proxies are hosted on the same server.

### Concurrent Testing

Proxy Reaper utilizes ThreadPoolExecutor for efficient concurrent proxy testing. You can control the number of concurrent connections with the `-c` or `--concurrent` parameter:

```bash
python proxyreaper.py https://www.google.com -p proxies.txt -c 20
```

### Automatic Proxy List Downloads

The automatic mode (`-A` or `--automatic-mode`) allows Proxy Reaper to download proxy lists from URLs specified in the configuration file:

```bash
python proxyreaper.py https://www.google.com -A
```

This feature is useful for maintaining an up-to-date proxy list without manual intervention.

### Detailed Debug Output

Enable detailed debugging information with the `-d` or `--debug` flag:

```bash
python proxyreaper.py https://www.google.com -p proxies.txt -d
```

This will show additional information such as HTTP headers, connection details, and more.

## Troubleshooting

### Common Issues and Solutions

#### 1. No valid proxies found

- Check that your proxy list file exists and has the correct format
- Ensure that each proxy is on a separate line
- If using automatic mode, check that the URLs in the configuration file are accessible

#### 2. Connection errors

- Increase the timeout value with `-t` or in the configuration file
- Check your internet connection
- Verify that the test URL is accessible from your location

#### 3. Performance issues

- Reduce the number of concurrent connections if your system has limited resources
- Use the debug mode to identify bottlenecks
- Consider using smaller proxy lists for testing

## Examples

### Basic Testing

```bash
# Test a single proxy against Google
python proxyreaper.py https://www.google.com -p 1.2.3.4:8080

# Test multiple proxies with increased timeout
python proxyreaper.py https://www.google.com -p proxies.txt -t 10

# Test proxies against a specific website
python proxyreaper.py https://www.example.com -p proxies.txt
```

### Filtering and Output

```bash
# Only consider proxies with response time under 500ms as "FAST"
python proxyreaper.py https://www.google.com -p proxies.txt -R 500

# Save only fast proxies to a CSV file
python proxyreaper.py https://www.google.com -p proxies.txt -o csv -f

# Save results to an SQLite database
python proxyreaper.py https://www.google.com -p proxies.txt -o sqlite
```

### Advanced Usage

```bash
# Enable debug mode for detailed information
python proxyreaper.py https://www.google.com -p proxies.txt -d

# Use automatic mode to download proxies from configured URLs
python proxyreaper.py https://www.google.com -A

# Run with 20 concurrent connections and detailed output
python proxyreaper.py https://www.google.com -p proxies.txt -c 20 -d

# Create a default configuration file
python proxyreaper.py --config
```

## License

MIT License

## Author

[Robert Tulke/rtulke]
