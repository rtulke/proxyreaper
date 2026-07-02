# Proxy Reaper

![Proxy Reaper Banner](https://raw.githubusercontent.com/rtulke/proxyreaper/main/demo/proxyreaper.gif)

Proxy Reaper is a powerful tool for checking proxy servers for availability, speed, and anonymity.
It supports HTTP, HTTPS, SOCKS4, and SOCKS5, categorizes proxies by response-time and anonymity
level, resolves GeoIP (and optionally reverse DNS), and exports the results to JSON, CSV, SQLite,
and plain-text.

## Table of Contents

1. [Features](#features)
2. [Installation](#installation)
3. [Installing OS-wide (Debian-based)](#installing-os-wide-debian-based)
4. [Basic Usage](#basic-usage)
5. [Command Line Arguments](#command-line-arguments)
6. [Filtering](#filtering)
7. [Configuration File](#configuration-file)
8. [Proxy Formats and Sources](#proxy-formats-and-sources)
9. [Speed Categories](#speed-categories)
10. [Anonymity Levels](#anonymity-levels)
11. [Output Formats](#output-formats)
12. [How It Works](#how-it-works)
13. [Troubleshooting](#troubleshooting)
14. [Examples](#examples)
15. [Reference Proxy Lists](#reference-proxy-lists)
16. [License](#license)

## Features

- Concurrent checking of many proxies (`ThreadPoolExecutor`)
- HTTP, HTTPS, SOCKS4, SOCKS5 — every protocol tested with a real request through the proxy
- Response-time measurement with automatic speed categories (ultrafast / fast / medium / slow)
- Anonymity-level detection (high anonymous, anonymous, header leak, transparent)
- GeoIP lookup (country, city) with caching; optional reverse-DNS lookup
- Powerful result filtering by speed, anonymity, protocol, country, and TLD
- Export to JSON, CSV, SQLite — plus an always-written `.txt` of working proxies
- Automatic proxy-list downloads from configured URLs
- Crash-safe autosave and graceful save on Ctrl-C
- Colored console output

## Installation

### Prerequisites

- Python 3.6 or higher
- Python packages: `requests`, `PySocks`, `colorama`

### Download

```bash
# Clone the repository
git clone https://github.com/rtulke/proxyreaper.git
cd proxyreaper

# Or download the script directly
wget https://raw.githubusercontent.com/rtulke/proxyreaper/main/proxyreaper.py
chmod +x proxyreaper.py
```

### Install dependencies

```bash
pip install requests PySocks colorama
```

or use the `requirements.txt` file inside a virtual environment:

**Linux / macOS**
```bash
cd proxyreaper
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Windows**
```bash
cd proxyreaper
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Installing OS-wide (Debian-based)

Works on most Debian-based distributions (Debian, Ubuntu, Mint, Raspberry Pi OS, Kali Linux, …).

```bash
# download via git
sudo git clone https://github.com/rtulke/proxyreaper.git /opt/proxyreaper
cd /opt/proxyreaper
sudo chmod +x proxyreaper.py

# install dependencies
sudo apt install python3-requests python3-socks python3-colorama

# copy the script to /usr/local/bin
sudo cp proxyreaper.py /usr/local/bin/proxyreaper

# use it from any directory
proxyreaper -h

# generate a config file, then edit it
proxyreaper -C
vim ~/.proxyreaper.conf
```

## Basic Usage

```bash
# Test a single proxy against a URL
python proxyreaper.py https://www.google.com -p 1.2.3.4:8080

# Test a list of proxies from a file
python proxyreaper.py https://www.google.com -p proxies.txt

# Test proxies from several files via a glob pattern
python proxyreaper.py https://www.google.com -p "lists/*.txt"

# Automatic mode: download lists from the URLs in [proxysources]
python proxyreaper.py https://www.google.com -A

# Create a default configuration file at ~/.proxyreaper.conf
python proxyreaper.py -C
```

If no `url` is given, the value from the config (`test_url`, default `https://www.google.com`) is
used. Either `-p/--proxy` or `-A/--automatic-mode` is required.

## Command Line Arguments

| Argument | Description |
|----------|-------------|
| `url` | URL to test the proxies against (optional; falls back to config `test_url`) |
| `-p, --proxy` | Proxy, comma-separated list, `.txt` file, or glob pattern |
| `-t, --timeout` | Timeout in seconds (default from config: 5) |
| `-o, --output` | Save format: `json`, `csv`, or `sqlite` (default: `csv`) |
| `-c, --concurrent` | Number of concurrent checks (default from config: 10) |
| `-d, --debug` | Enable detailed debug output (headers, per-proxy errors) |
| `-l, --reverse-lookup` | Resolve each proxy IP via reverse DNS (slower) |
| `-A, --automatic-mode` | Download proxy lists from the configured URLs |
| `-C, --config` | Create a default config file at `~/.proxyreaper.conf` |
| `-v, --version` | Display version and exit |
| `--filter-status` | Keep only these speed categories (see [Filtering](#filtering)) |
| `--filter-anonymity` | Keep only these anonymity levels |
| `--filter-protocol` | Keep only these protocols |
| `--filter-country` | Keep only these country codes (via GeoIP) |
| `--filter-tld` | Keep only these country TLDs (via GeoIP) |

> Note: a plain-text file of the working proxies is **always** written in addition to the `-o` format;
> `txt` is not a separate `-o` value.

## Filtering

Filters restrict what gets written to the output files (they do not change what is tested). All
filter options accept multiple values, and they combine (logical AND across categories).

```bash
# Only ultrafast + fast SOCKS5 proxies
python proxyreaper.py -p proxies.txt --filter-status ultrafast fast --filter-protocol socks5

# Only high-anonymous proxies located in Germany or the US
python proxyreaper.py -p proxies.txt --filter-anonymity highanonymous --filter-country de us
```

| Option | Allowed values |
|--------|----------------|
| `--filter-status` | `ultrafast` `fast` `medium` `slow` |
| `--filter-anonymity` | `highanonymous` `anonymous` `headerleak` `transparent` |
| `--filter-protocol` | `http` `https` `socks4` `socks5` |
| `--filter-country` | country codes, e.g. `de us uk` |
| `--filter-tld` | country TLDs, e.g. `de us uk` |

When any filter is active, output filenames are prefixed with `filtered_proxies_...`; otherwise
`proxy_results_...`.

## Configuration File

Configuration files are searched in this order (later ones override earlier ones):

1. Built-in defaults
2. `/etc/proxyreaper.conf` (system-wide)
3. `~/.proxyreaper.conf` (user-specific)

Command-line arguments override the configuration. Create a default file with:

```bash
python proxyreaper.py -C
```

### Format

```ini
[general]
timeout = 5
concurrent = 10
test_url = https://www.google.com

[output]
format = json
fast_only = false
save_directory = results

[proxysources]
urls = https://example.com/list1.txt, https://example.com/list2.txt

[advanced]
debug = false
anonymity_check_url = https://httpbin.org/get
```

| Section / key | Meaning |
|---------------|---------|
| `general.timeout` | Connection/read timeout in seconds (default: 5) |
| `general.concurrent` | Number of concurrent checks (default: 10) |
| `general.test_url` | Default URL to test proxies against |
| `output.save_directory` | Directory for result files (default: `results`) |
| `proxysources.urls` | Comma-separated list of proxy-list URLs for `-A` mode |
| `advanced.debug` | Enable debug output by default |
| `advanced.anonymity_check_url` | Endpoint used for the anonymity check (must echo IP + headers, like httpbin) |

> The default output format when `-o` is omitted is **CSV**. `output.format` and `output.fast_only`
> are retained for compatibility but are not the primary controls; use `-o` and the `--filter-*`
> options.

## Proxy Formats and Sources

Supported proxy formats (duplicates are removed automatically, order preserved):

- `host:port` — defaults to the `http` protocol, e.g. `127.0.0.1:8080`
- `protocol://host:port` — e.g. `socks5://127.0.0.1:1080`
- `protocol://username:password@host:port` — e.g. `http://user:pass@127.0.0.1:8080`

Input methods:

1. **Single proxy**: `-p 127.0.0.1:8080`
2. **Comma-separated list**: `-p "127.0.0.1:8080,192.168.1.1:3128"`
3. **Text file**: `-p proxies.txt` (one proxy per line; lines starting with `#` are ignored)
4. **Glob pattern**: `-p "lists/*.txt"` (all matching files are merged)
5. **Automatic download**: `-A` (URLs from `[proxysources]`)

### Example proxy list

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

## Speed Categories

Working proxies are categorized by measured response time:

| Category | Response time |
|----------|---------------|
| `ultrafast` | < 100 ms |
| `fast` | 100–500 ms |
| `medium` | 500–1000 ms |
| `slow` | > 1000 ms |

Non-working proxies get `status = FAILED` (working proxies get `status = working`).

## Anonymity Levels

| Level | Color | Description |
|-------|-------|-------------|
| **High Anonymous** | Green (bright) | Your IP and the fact you use a proxy are both hidden |
| **Anonymous** | Blue (bright) | Your IP is hidden, but the server can tell a proxy is used |
| **Anonymous (Header leak)** | Yellow | Your IP is hidden, but proxy headers are visible |
| **Transparent** | Red | Your original IP is visible to the server |

Anonymity is determined by requesting `anonymity_check_url` through the proxy and comparing the
returned IP and headers (`via`, `forwarded`, `x-forwarded`, …) against your real public IP.

## Output Formats

Results are written to `save_directory` (default `results/`). A plain-text file of working proxies
is always written in addition to the chosen `-o` format.

Each result record contains: `proxy`, `hostname`, `status`, `speed_category`, `response_time`,
`country`, `city`, `anonymity`, `protocol`, `check_time`.

### JSON (`-o json`)

```json
[
  {
    "proxy": "http://192.168.1.1:8080",
    "hostname": "192.168.1.1",
    "status": "working",
    "speed_category": "fast",
    "response_time": 345.67,
    "country": "United States",
    "city": "New York",
    "anonymity": "High Anonymous",
    "protocol": "http",
    "check_time": "2026-07-02 15:30:45"
  }
]
```

### CSV (`-o csv`, default)

```
proxy,hostname,status,speed_category,response_time,country,city,anonymity,protocol,check_time
http://192.168.1.1:8080,192.168.1.1,working,fast,345.67,United States,New York,High Anonymous,http,2026-07-02 15:30:45
```

### SQLite (`-o sqlite`)

Creates a database with a `proxies` table for more complex queries and analysis.

### Text (always)

A `*.txt` file listing only the working proxies, one per line — easy to reuse in other tools.

## How It Works

- **Fail-fast checking**: each proxy is first tested for connectivity/speed; the more expensive
  GeoIP, reverse-DNS, and anonymity lookups run only for proxies that actually work.
- **Real per-protocol requests**: HTTP/HTTPS and SOCKS4/SOCKS5 are all measured with a real request
  routed through the proxy (SOCKS via PySocks), so timings are directly comparable.
- **GeoIP caching**: geo results are cached (thread-safe) to avoid repeated lookups for proxies on
  the same host.
- **Autosave & Ctrl-C**: intermediate results are written to a single rolling
  `results/proxy_results_partial.json` every few proxies; interrupting with Ctrl-C saves a final
  snapshot before exiting, so progress is not lost.

## Troubleshooting

**No valid proxies found**
- Check the file exists and each proxy is on its own line
- In automatic mode, confirm the `[proxysources]` URLs are reachable

**Connection errors**
- Increase the timeout with `-t` or in the config
- Verify the test URL is reachable from your location

**Performance / rate limits**
- Reduce concurrency with `-c` on limited machines
- GeoIP endpoints are public and rate-limited; very large lists may get throttled

## Examples

```bash
# Test a list with an increased timeout, save as JSON
python proxyreaper.py https://www.google.com -p proxies.txt -t 10 -o json

# 20 concurrent workers with debug output
python proxyreaper.py https://www.google.com -p proxies.txt -c 20 -d

# Reverse-DNS + only high-anonymous SOCKS5 proxies, saved to SQLite
python proxyreaper.py -p proxies.txt -l -o sqlite \
    --filter-protocol socks5 --filter-anonymity highanonymous

# Download fresh lists and keep only fast German proxies
python proxyreaper.py -A --filter-status ultrafast fast --filter-country de
```

## Reference Proxy Lists

- https://github.com/roosterkid/openproxylist
- https://github.com/TheSpeedX/PROXY-List
- https://github.com/monosans/proxy-list
- https://github.com/vakhov/fresh-proxy-list
- https://github.com/proxifly/free-proxy-list
- https://github.com/topics/proxy-list

## License

MIT License

## Author

Robert Tulke ([rtulke](https://github.com/rtulke))
