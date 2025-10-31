## Proxy Reaper - Documentation

![Proxy Reaper Banner](https://raw.githubusercontent.com/rtulke/proxyreaper/main/demo/proxyreaper.gif)

Proxy Reaper is a powerful tool for checking proxy servers for availability, speed and anonymity. It supports various protocols such as HTTP, HTTPS, SOCKS4, and SOCKS5, and offers enhanced features for managing and testing proxies efficiently.

## Table of Contents

1. [Installation](#installation)
2. [Installing OS wide (Debian based Distributions)](#installing-os-wide)
3. [Basic Usage](#basic-usage)
4. [Command Line Arguments](#command-line-arguments)
5. [Configuration File](#configuration-file)
6. [Proxy Formats and Sources](#proxy-formats-and-sources)
7. [Speed Categories](#speed-categories)
8. [Anonymity Levels](#anonymity-levels)
9. [Filter Options](#filter-options)
10. [Output Formats](#output-formats)
11. [Advanced Features](#advanced-features)
12. [Troubleshooting](#troubleshooting)
13. [Examples](#examples)

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
source venv/bin/activate
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
cd ~

# create dev directory for development stuff if needed
mkdir dev
cd dev

# download via git
git clone https://github.com/rtulke/proxyreaper.git
cd proxyreaper
chmod +x proxyreaper.py

# install dependencies
apt install python3-socks python3-colorama

# copy proxyreaper script to `/usr/local/bin`
cp proxyreaper.py /usr/local/bin/proxyreaper

# install man page and updating mandb
cp proxyreaper.1 /usr/local/share/man/man1/
mandb

# use the proxyreaper script from any directory
proxyreaper -h

# generate new config file
proxyreaper --config

# you can also try to edit the new generated configuration file
vim ~/.proxyreaper.conf

# try using the manual
man proxyreaper
```


## Basic Usage

```bash
# Test a single proxy
python proxyreaper.py https://www.google.com -p 1.2.3.4:8080

# Test multiple proxies from a file
python proxyreaper.py https://www.google.com -p proxies.txt

# Test multiple files using glob patterns
python proxyreaper.py https://www.google.com -p "proxies/*.txt"

# Create a default configuration file
python proxyreaper.py --config

# Use automatic mode to download proxies from URLs defined in config [proxysources]
python proxyreaper.py https://www.google.com -A

# Filter and save only ultrafast proxies from Germany
python proxyreaper.py https://www.google.com -p proxies.txt --filter-status ultrafast --filter-country de
```

## Command Line Arguments

### Core Arguments

| Argument | Short | Type | Description |
|----------|-------|------|-------------|
| `url` | - | positional | URL to test the proxies against |
| `--proxy` | `-p` | string | Proxy, file with proxies, or glob pattern (e.g., `*.txt`, `proxies[1-5].txt`) |
| `--timeout` | `-t` | integer | Timeout in seconds (default from config) |
| `--output` | `-o` | choice | Save results format: `json`, `csv`, or `sqlite` (default: `csv`) |
| `--response-time` | `-R` | float | Filter for fast proxies (maximum response time in milliseconds) |
| `--concurrent` | `-c` | integer | Number of concurrent checks (default: 10) |
| `--debug` | `-d` | flag | Enable detailed debug output |
| `--version` | `-v` | flag | Display version information and exit |
| `--automatic-mode` | `-A` | flag | Download proxy lists from configured URLs |
| `--config` | `-C` | flag | Create default config file in `~/.proxyreaper.conf` |
| `--reverse-lookup` | `-l` | flag | Enable reverse DNS lookup for proxy IPs (slower but shows hostnames) |

### Filter Arguments

| Argument | Type | Values | Description |
|----------|------|--------|-------------|
| `--filter-status` | multi | `ultrafast`, `fast`, `medium`, `slow` | Filter by speed category (can combine multiple) |
| `--filter-anonymity` | multi | `highanonymous`, `anonymous`, `headerleak`, `transparent` | Filter by anonymity level (can combine multiple) |
| `--filter-protocol` | multi | `http`, `https`, `socks4`, `socks5` | Filter by protocol type (can combine multiple) |
| `--filter-country` | multi | ISO codes | Filter by country code, e.g., `de us uk fr` (can combine multiple) |
| `--filter-tld` | multi | country codes | Filter by country TLD based on GeoIP, e.g., `de us uk` (can combine multiple) |

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
format = csv
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
- `response_time_filter`: Maximum response time in milliseconds for filtering (default: 1000)
- `test_url`: URL to use for testing proxies (default: https://www.google.com)

#### [output]

- `format`: Default output format - `json`, `csv`, or `sqlite` (default: `csv`)
- `save_directory`: Directory to save results (default: `results`)

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

#### 1. Single Proxy
Directly specify a proxy on the command line:
```bash
python proxyreaper.py https://www.google.com -p 127.0.0.1:8080
```

#### 2. Multiple Proxies (Comma-separated)
Use comma-separated list:
```bash
python proxyreaper.py https://www.google.com -p "127.0.0.1:8080,192.168.1.1:3128"
```

#### 3. Single Text File
Provide a file with one proxy per line:
```bash
python proxyreaper.py https://www.google.com -p proxies.txt
```

#### 4. Multiple Files (Glob Patterns)
Use glob patterns to match multiple files:

```bash
# All .txt files in a directory
python proxyreaper.py https://www.google.com -p "proxies/*.txt"

# Files matching a specific pattern
python proxyreaper.py https://www.google.com -p "proxylist*.txt"

# Files with numbered ranges
python proxyreaper.py https://www.google.com -p "proxylist[1-5].txt"

# Complex patterns
python proxyreaper.py https://www.google.com -p "../sources/proxy_*.txt"
```

Supported glob patterns:
- `*` - Matches any characters
- `?` - Matches single character
- `[1-5]` - Matches range of characters
- `[abc]` - Matches specific characters

#### 5. Automatic Download
Use automatic mode to download proxies from URLs specified in the configuration:
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

## Speed Categories

Proxy Reaper categorizes proxies into four speed categories based on their response time:

| Category | Response Time | Description | Use Case |
|----------|---------------|-------------|----------|
| **Ultrafast** | < 100ms | Extremely fast proxies | Real-time applications, streaming, gaming |
| **Fast** | 100-500ms | Fast proxies | Web browsing, API calls, general use |
| **Medium** | 500-1000ms | Medium speed proxies | Background tasks, batch processing |
| **Slow** | > 1000ms | Slow proxies | Non-time-critical tasks |

### Speed Category Output

The speed category is included in all output formats:

**CSV Output:**
```csv
proxy,hostname,status,speed_category,response_time,country,city,anonymity,protocol,check_time
http://1.2.3.4:8080,1.2.3.4,working,ultrafast,87.5,Germany,Berlin,High Anonymous,http,2025-10-31 14:30:45
```

**Console Output:**
```
[1/100] ULTRAFAST - http://1.2.3.4:8080 (Germany, Berlin, High Anonymous) - 87 ms
[2/100] FAST - http://5.6.7.8:3128 (United States, New York, Anonymous) - 245 ms
[3/100] SLOW - http://9.10.11.12:8080 (France, Paris, Transparent) - 1523 ms
```

## Anonymity Levels

Proxy Reaper categorizes proxies into different anonymity levels and uses color coding for easy identification:

| Level | Color | Description | Headers Visible |
|-------|-------|-------------|-----------------|
| **High Anonymous** | Green (Bright) | Your IP address and proxy status are completely hidden | No proxy headers |
| **Anonymous** | Blue (Bright) | Your IP address is hidden, but the server knows you're using a proxy | Minimal proxy headers |
| **Anonymous (Header leak)** | Yellow | Your IP is hidden, but proxy headers are visible | Proxy headers visible |
| **Transparent** | Red | Your original IP address is visible to the server | All headers visible |

### How Anonymity is Determined

1. **High Anonymous**: The proxy changes your IP and doesn't add proxy-related headers
2. **Anonymous**: The proxy changes your IP but adds minimal headers revealing it's a proxy
3. **Anonymous (Header leak)**: The proxy changes your IP but adds headers that reveal proxy details
4. **Transparent**: The proxy doesn't hide your original IP address or forwards it in headers

## Filter Options

Proxy Reaper provides powerful filtering capabilities to save only the proxies that meet your specific requirements. Filters are applied when saving results and create descriptive filenames.

### Filter Behavior

- **Multiple values within same filter**: OR logic (any match passes)
- **Multiple different filters**: AND logic (all must match)
- **Working proxies only**: Failed proxies are automatically excluded

### Speed Status Filter

Filter proxies by their speed category:

```bash
# Save only ultrafast proxies
python proxyreaper.py https://www.google.com -p proxies.txt --filter-status ultrafast

# Save ultrafast OR fast proxies
python proxyreaper.py https://www.google.com -p proxies.txt --filter-status ultrafast fast

# Save medium OR slow proxies
python proxyreaper.py https://www.google.com -p proxies.txt --filter-status medium slow
```

**Available values:** `ultrafast`, `fast`, `medium`, `slow`

### Anonymity Filter

Filter proxies by their anonymity level:

```bash
# Save only high anonymous proxies
python proxyreaper.py https://www.google.com -p proxies.txt --filter-anonymity highanonymous

# Save high anonymous OR anonymous proxies
python proxyreaper.py https://www.google.com -p proxies.txt --filter-anonymity highanonymous anonymous

# Exclude transparent proxies (save all except transparent)
python proxyreaper.py https://www.google.com -p proxies.txt --filter-anonymity highanonymous anonymous headerleak
```

**Available values:** `highanonymous`, `anonymous`, `headerleak`, `transparent`

### Protocol Filter

Filter proxies by their protocol:

```bash
# Save only HTTP proxies
python proxyreaper.py https://www.google.com -p proxies.txt --filter-protocol http

# Save HTTP OR HTTPS proxies
python proxyreaper.py https://www.google.com -p proxies.txt --filter-protocol http https

# Save only SOCKS proxies
python proxyreaper.py https://www.google.com -p proxies.txt --filter-protocol socks4 socks5
```

**Available values:** `http`, `https`, `socks4`, `socks5`

### Country Filter

Filter proxies by their country location (based on GeoIP):

```bash
# Save only German proxies
python proxyreaper.py https://www.google.com -p proxies.txt --filter-country de

# Save German OR US proxies
python proxyreaper.py https://www.google.com -p proxies.txt --filter-country de us

# Save European proxies
python proxyreaper.py https://www.google.com -p proxies.txt --filter-country de fr uk nl it es
```

**Supported country codes:** ISO 3166-1 alpha-2 codes (e.g., `de`, `us`, `uk`, `fr`, `jp`, `cn`, etc.)

Full list of ~150 supported countries available in the code.

### TLD Filter

Filter proxies by country TLD based on GeoIP location:

```bash
# Save proxies from .de domains (German IPs)
python proxyreaper.py https://www.google.com -p proxies.txt --filter-tld de

# Save proxies from .de OR .us domains
python proxyreaper.py https://www.google.com -p proxies.txt --filter-tld de us
```

**Note:** TLD filtering is based on GeoIP country mapping, not actual domain names.

### Combining Filters

Combine multiple filters for precise proxy selection:

```bash
# Ultrafast, high anonymous proxies from Germany
python proxyreaper.py https://www.google.com -p proxies.txt \
  --filter-status ultrafast \
  --filter-anonymity highanonymous \
  --filter-country de

# Fast HTTP/HTTPS proxies from US or UK
python proxyreaper.py https://www.google.com -p proxies.txt \
  --filter-status ultrafast fast \
  --filter-protocol http https \
  --filter-country us uk

# High anonymous SOCKS5 proxies from Europe (any speed)
python proxyreaper.py https://www.google.com -p proxies.txt \
  --filter-anonymity highanonymous \
  --filter-protocol socks5 \
  --filter-country de fr uk nl it es
```

### Filter Output Filenames

When filters are applied, the output filename includes filter information:

```bash
# Without filters:
results/proxy_results_20251031_143045.csv

# With filters:
results/filtered_proxies_ultrafast_highanonymous_http_https_de_us_20251031_143045.csv
```

This makes it easy to identify which filters were used for each result file.

## Output Formats

Proxy Reaper supports multiple output formats. The default format is **CSV** if no `-o` option is specified.

### CSV Output (Default)

```bash
# Uses CSV by default
python proxyreaper.py https://www.google.com -p proxies.txt

# Explicitly specify CSV
python proxyreaper.py https://www.google.com -p proxies.txt -o csv
```

Creates a CSV file with detailed proxy information:

```csv
proxy,hostname,status,speed_category,response_time,country,city,anonymity,protocol,check_time
http://1.2.3.4:8080,proxy.example.com,working,ultrafast,87.5,Germany,Berlin,High Anonymous,http,2025-10-31 14:30:45
http://5.6.7.8:3128,5.6.7.8,working,fast,245.3,United States,New York,Anonymous,http,2025-10-31 14:30:46
```

### JSON Output

```bash
python proxyreaper.py https://www.google.com -p proxies.txt -o json
```

Creates a JSON file with detailed proxy information:

```json
[
  {
    "proxy": "http://1.2.3.4:8080",
    "hostname": "proxy.example.com",
    "status": "working",
    "speed_category": "ultrafast",
    "response_time": 87.5,
    "country": "Germany",
    "city": "Berlin",
    "anonymity": "High Anonymous",
    "protocol": "http",
    "check_time": "2025-10-31 14:30:45"
  }
]
```

### SQLite Output

```bash
python proxyreaper.py https://www.google.com -p proxies.txt -o sqlite
```

Creates an SQLite database with a `proxies` table containing the proxy information. This is useful for more complex queries and data analysis.

**Database schema:**
```sql
CREATE TABLE proxies (
    proxy TEXT,
    hostname TEXT,
    status TEXT,
    speed_category TEXT,
    response_time REAL,
    country TEXT,
    city TEXT,
    anonymity TEXT,
    protocol TEXT,
    check_time TEXT
);
```

### Text Output

In addition to the specified format, Proxy Reaper **always creates a plain text file** with just the working proxies (one per line), which can be easily used in other applications:

```
http://1.2.3.4:8080
http://5.6.7.8:3128
socks5://9.10.11.12:1080
```

## Advanced Features

### Reverse DNS Lookup

Enable reverse DNS lookup to resolve proxy IPs to hostnames:

```bash
python proxyreaper.py https://www.google.com -p proxies.txt -l
```

**Output without `-l`:**
```
[1/100] ULTRAFAST - http://1.2.3.4:8080 (Germany, Berlin, High Anonymous) - 87 ms
```

**Output with `-l`:**
```
[1/100] ULTRAFAST - proxy.example.com (Germany, Berlin, High Anonymous) - 87 ms
```

The hostname is also saved in the output files:
- CSV: `hostname` column
- JSON: `hostname` field
- Text: unchanged (still shows proxy URL)

**Note:** Reverse DNS lookup is slower as it performs additional DNS queries. Use only when needed.

### Glob Pattern Support

Load proxies from multiple files using glob patterns:

```bash
# All .txt files in directory
python proxyreaper.py https://www.google.com -p "proxies/*.txt"

# Specific pattern
python proxyreaper.py https://www.google.com -p "proxylist_*.txt"

# Numbered files
python proxyreaper.py https://www.google.com -p "proxylist[1-9].txt"

# Range
python proxyreaper.py https://www.google.com -p "proxy_[a-z].txt"
```

**Console output:**
```
Found 15 file(s) matching pattern: proxies/*.txt
Loaded 450 proxies from proxy_http.txt
Loaded 230 proxies from proxy_socks.txt
...
Total: Loaded 1250 proxies from 15 file(s)
```

### Automatic Saving During Execution

Proxy Reaper automatically saves intermediate results every 5 proxies checked. This ensures that even if the program is interrupted, you won't lose your progress.

Autosave files are stored in the `results` directory:
- `proxy_results_TIMESTAMP_final.json` - Complete autosave

### GeoIP Caching

To improve performance and reduce API calls, Proxy Reaper caches geographical information for IP addresses. This significantly speeds up testing when multiple proxies are hosted on the same server or subnet.

### Concurrent Testing

Proxy Reaper utilizes ThreadPoolExecutor for efficient concurrent proxy testing. You can control the number of concurrent connections with the `-c` or `--concurrent` parameter:

```bash
# Test with 20 concurrent workers
python proxyreaper.py https://www.google.com -p proxies.txt -c 20

# Test with 50 concurrent workers (for large lists)
python proxyreaper.py https://www.google.com -p proxies.txt -c 50
```

**Performance recommendations:**
- Default: 10 workers (balanced)
- Small lists (<100): 5-10 workers
- Medium lists (100-1000): 10-20 workers
- Large lists (>1000): 20-50 workers

### Automatic Proxy List Downloads

The automatic mode (`-A` or `--automatic-mode`) allows Proxy Reaper to download proxy lists from URLs specified in the configuration file:

```bash
python proxyreaper.py https://www.google.com -A
```

This feature is useful for maintaining an up-to-date proxy list without manual intervention.

**Configuration example:**
```ini
[proxysources]
urls = https://raw.githubusercontent.com/user/proxy-list/main/http.txt,
       https://www.proxy-list.download/api/v1/get?type=http,
       https://api.proxyscrape.com/v2/?request=get&protocol=http
```

### Detailed Debug Output

Enable detailed debugging information with the `-d` or `--debug` flag:

```bash
python proxyreaper.py https://www.google.com -p proxies.txt -d
```

Debug mode shows:
- HTTP headers and responses
- Connection details
- Error messages with stack traces
- GeoIP API calls
- File operations
- Proxy validation details

## Troubleshooting

### Common Issues and Solutions

#### 1. No valid proxies found

**Symptoms:**
```
No valid proxies found after validation.
Exiting.
```

**Solutions:**
- Check that your proxy list file exists and has the correct format
- Ensure that each proxy is on a separate line
- Verify proxy format: `protocol://host:port` or `host:port`
- If using glob patterns, check that the pattern matches existing files
- If using automatic mode, check that the URLs in the configuration file are accessible

#### 2. No files matched pattern

**Symptoms:**
```
No files matched pattern: proxies/*.txt
```

**Solutions:**
- Verify the glob pattern is correct
- Check that files exist in the specified directory
- Use absolute paths or verify current working directory
- Ensure file extensions match (e.g., `.txt` not `.TXT`)

#### 3. Connection errors

**Symptoms:**
```
[1/100] FAILED - http://1.2.3.4:8080
```

**Solutions:**
- Increase the timeout value with `-t` or in the configuration file
- Check your internet connection
- Verify that the test URL is accessible from your location
- Try a different test URL
- Some proxies may be genuinely offline

#### 4. Performance issues

**Symptoms:**
- Slow proxy checking
- High CPU or memory usage
- System slowdown

**Solutions:**
- Reduce the number of concurrent connections: `-c 5`
- Use smaller proxy lists for testing
- Increase timeout for slow networks
- Disable reverse DNS lookup (remove `-l`)
- Use debug mode to identify bottlenecks: `-d`

#### 5. ImportError or ModuleNotFoundError

**Symptoms:**
```
ModuleNotFoundError: No module named 'requests'
```

**Solutions:**
- Install required dependencies: `pip install requests PySocks colorama`
- Activate virtual environment if using one: `source venv/bin/activate`
- Verify Python version: `python --version` (3.6+ required)

#### 6. Permission denied errors

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: 'results/proxy_results.csv'
```

**Solutions:**
- Check write permissions for the output directory
- Create the output directory manually: `mkdir results`
- Change output directory in config or use `-o` flag
- Run with appropriate permissions

## Examples

### Basic Testing

```bash
# Test a single proxy against Google
python proxyreaper.py https://www.google.com -p 1.2.3.4:8080

# Test multiple proxies with increased timeout
python proxyreaper.py https://www.google.com -p proxies.txt -t 10

# Test proxies against a specific website
python proxyreaper.py https://www.example.com -p proxies.txt

# Test all proxy files in a directory
python proxyreaper.py https://www.google.com -p "proxy_sources/*.txt"
```

### Speed and Performance

```bash
# Only consider proxies with response time under 500ms as "FAST"
python proxyreaper.py https://www.google.com -p proxies.txt -R 500

# Test with 30 concurrent workers for faster processing
python proxyreaper.py https://www.google.com -p proxies.txt -c 30

# Combine for maximum performance
python proxyreaper.py https://www.google.com -p proxies.txt -c 50 -t 3
```

### Filtering Examples

```bash
# Save only ultrafast proxies
python proxyreaper.py https://www.google.com -p proxies.txt --filter-status ultrafast

# Save only high anonymous proxies
python proxyreaper.py https://www.google.com -p proxies.txt --filter-anonymity highanonymous

# Save only HTTP and HTTPS proxies
python proxyreaper.py https://www.google.com -p proxies.txt --filter-protocol http https

# Save only German proxies
python proxyreaper.py https://www.google.com -p proxies.txt --filter-country de

# Save ultrafast, high anonymous proxies from Germany or US
python proxyreaper.py https://www.google.com -p proxies.txt \
  --filter-status ultrafast \
  --filter-anonymity highanonymous \
  --filter-country de us

# Save fast HTTP proxies from Europe
python proxyreaper.py https://www.google.com -p proxies.txt \
  --filter-status ultrafast fast \
  --filter-protocol http \
  --filter-country de fr uk nl it es pl
```

### Output Format Examples

```bash
# Save as CSV (default)
python proxyreaper.py https://www.google.com -p proxies.txt

# Save as JSON
python proxyreaper.py https://www.google.com -p proxies.txt -o json

# Save as SQLite database
python proxyreaper.py https://www.google.com -p proxies.txt -o sqlite

# Filter and save as JSON
python proxyreaper.py https://www.google.com -p proxies.txt \
  --filter-status ultrafast \
  -o json
```

### Advanced Usage

```bash
# Enable debug mode for detailed information
python proxyreaper.py https://www.google.com -p proxies.txt -d

# Use automatic mode to download proxies from configured URLs
python proxyreaper.py https://www.google.com -A

# Use automatic mode with specific URLs
python proxyreaper.py https://www.google.com -A -p "https://example.com/proxies.txt,https://example2.com/list.txt"

# Run with reverse DNS lookup
python proxyreaper.py https://www.google.com -p proxies.txt -l

# Comprehensive test with all features
python proxyreaper.py https://www.google.com \
  -p "proxy_sources/*.txt" \
  -c 30 \
  -t 10 \
  -l \
  --filter-status ultrafast fast \
  --filter-anonymity highanonymous \
  --filter-country de us uk \
  -o json \
  -d
```

### Practical Scenarios

```bash
# Find the fastest German proxies for web scraping
python proxyreaper.py https://www.google.com -p proxies.txt \
  --filter-status ultrafast fast \
  --filter-country de \
  -o csv

# Get high anonymous SOCKS5 proxies for secure browsing
python proxyreaper.py https://www.google.com -p proxies.txt \
  --filter-anonymity highanonymous \
  --filter-protocol socks5 \
  -o json

# Build a database of all working European proxies
python proxyreaper.py https://www.google.com -p "europe/*.txt" \
  --filter-country de fr uk nl it es pl cz at ch \
  -o sqlite

# Quick test of premium proxy list with hostname resolution
python proxyreaper.py https://www.google.com \
  -p premium_proxies.txt \
  -l \
  -c 20 \
  --filter-status ultrafast \
  --filter-anonymity highanonymous

# Daily automated proxy harvesting
python proxyreaper.py https://www.google.com -A \
  -c 50 \
  --filter-status ultrafast fast medium \
  --filter-anonymity highanonymous anonymous \
  -o sqlite
```

## License

MIT License

## Author

[Robert Tulke/rtulke]
