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

# Contributing

```
pip install pre-commit
pre-commit run --files check_trex.py
```
