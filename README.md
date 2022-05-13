# check_trex

Nagios check for [T-Rex miner](https://github.com/trexminer/T-Rex).

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
./check_trex --help
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
