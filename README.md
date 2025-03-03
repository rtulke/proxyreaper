# Proxy Reaper

![Proxy Reaper Banner](https://raw.githubusercontent.com/rtulke/proxyreaper/main/assets/banner.png)

Proxy Reaper is a powerful Python tool for checking proxy servers for availability, speed, and anonymity. The tool supports various protocols such as HTTP, HTTPS, SOCKS4, and SOCKS5.

I was looking into the subject of proxies a while ago and I noticed that many of the lists available on the Internet stopped working shortly after most of the proxies were published. This is quite annoying, especially if you have lists with over 11,000 proxies and now have to test them manually :D. 

So I wrote a tool to solve exactly this problem. It tests proxies.

## Features

- Concurrent checking of multiple proxies
- Support for HTTP, HTTPS, SOCKS4, and SOCKS5 protocols
- Response time measurement
- Anonymity level detection
- Geolocation (country, city)
- Export results as JSON, CSV, or TXT
- Filtering for fast proxies
- Colored console output

## Installation

```bash
# Clone the repository
git clone https://github.com/rtulke/proxyreaper.git
cd proxyreaper

# Install dependencies
pip install -r requirements.txt
```

### Requirements

- Python 3.6 or higher
- The following Python packages:
  - requests
  - PySocks
  - colorama

## Usage

### Basic Commands

```bash
# Show help
python proxyreaper2.py --help

# Show version
python proxyreaper2.py --version

# Test a single proxy
python proxyreaper2.py https://example.com -p 1.2.3.4:8080

# Test a list of proxies from a file
python proxyreaper2.py https://example.com -p proxies.txt

# Test multiple proxies separated by commas
python proxyreaper2.py https://example.com -p "1.2.3.4:8080,5.6.7.8:3128"
```

### Advanced Options

```bash
# Set timeout for proxy checks (in seconds)
python proxyreaper2.py https://example.com -p proxies.txt -t 10

# Save results as JSON
python proxyreaper2.py https://example.com -p proxies.txt -o json

# Save results as CSV
python proxyreaper2.py https://example.com -p proxies.txt -o csv

# Filter only fast proxies (with maximum response time in milliseconds)
python proxyreaper2.py https://example.com -p proxies.txt -R 500

# Save only fast proxies in the output
python proxyreaper2.py https://example.com -p proxies.txt -o json -f

# Adjust the number of concurrent checks
python proxyreaper2.py https://example.com -p proxies.txt -c 20
```

## Command Line Arguments

| Argument | Short Form | Description |
|----------|------------|-------------|
| `url` | - | URL to test the proxies |
| `--proxy` | `-p` | Proxy or file with proxies (comma-separated or .txt file) |
| `--timeout` | `-t` | Timeout in seconds (default: 5) |
| `--output` | `-o` | Save results as JSON or CSV |
| `--response-time` | `-R` | Filter for fast proxies (maximum response time in milliseconds) |
| `--version` | `-v` | Show version information |
| `--fast-only` | `-f` | Save only fast proxies in the output file |
| `--concurrent` | `-c` | Number of concurrent checks (default: 10) |

## Proxy Formats

The tool supports various proxy formats:

- IP:Port (e.g., `127.0.0.1:8080`)
- Protocol://IP:Port (e.g., `http://127.0.0.1:8080`)
- Protocol://Username:Password@IP:Port (e.g., `http://user:pass@127.0.0.1:8080`)

## Examples for Proxy Lists

A valid proxy list (proxies.txt) should look like this:

```
# HTTP proxies
http://1.2.3.4:8080
http://user:pass@5.6.7.8:3128

# HTTPS proxies
https://9.10.11.12:8443

# SOCKS proxies
socks4://13.14.15.16:1080
socks5://17.18.19.20:1080

# Without protocol (defaults to HTTP)
21.22.23.24:8080
```

## Output Formats

### JSON Output

The JSON output contains detailed information about each tested proxy:

```json
[
    {
        "proxy": "http://1.2.3.4:8080",
        "status": "FAST",
        "response_time": 350.45,
        "country": "Germany",
        "city": "Berlin",
        "anonymity": "Anonymous",
        "protocol": "http"
    },
    ...
]
```

### CSV Output

The CSV output contains the same information in tabular form:

```
proxy,status,response_time,country,city,anonymity,protocol
http://1.2.3.4:8080,FAST,350.45,Germany,Berlin,Anonymous,http
...
```

### TXT Output

The TXT output contains only the working proxies (one per line):

```
http://1.2.3.4:8080
http://5.6.7.8:3128
...
```

## Status Definitions

- **FAST**: The proxy works and meets the response time conditions.
- **SLOW**: The proxy works but is slower than the specified maximum response time.
- **FAILED**: The proxy doesn't work or exceeded the timeout.

## Anonymity Levels

- **Transparent**: The proxy reveals your original IP.
- **Anonymous (Header leak)**: The proxy hides your IP but reveals that it's a proxy.
- **Anonymous**: The proxy hides your IP and doesn't reveal that it's a proxy.

## Proxy Lists
- https://github.com/topics/proxy-list

## License

MIT License

## Author

[Robert Tulke /rtulke]
