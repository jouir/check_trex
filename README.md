# check_trex

Nagios check for [T-Rex miner](https://github.com/trexminer/T-Rex).

# Security

T-Rex API must be opened in a secured way:
* `--api-read-only`: accessible only in read-only, no modification
* `--api-bind-http 127.0.0.1:4067`: (default) accessible only to local connections

If the check is executed **remotely**, you should add a **firewall rule** to allow only the host running the check to
access the T-Rex API port.

**HTTPS** should be used:
* `--api-https`
* `--api-webserver-cert`
* `--api-webserver-pkey`

See full [list of options](https://github.com/trexminer/T-Rex#usage).

# Installation

Using pip:

```
python3 -m venv venv
. ./venv/bin/activate
pip install -r requirements.txt
```

Using debian package manager:

```
sudo apt-get install python3-nagiosplugin python3-requests
```

# Usage

```
./check_trex.py --help
```

# Examples

Nagios NRPE:

```
command[check_trex]=/opt/check_trex/check_trex.py --hashrate-warning 60000000 --hashrate-critical 50000000 --uptime-critical 300 --uptime-warning 600
```

# Contributing

```
pip install pre-commit
pre-commit run --files check_trex.py
```
