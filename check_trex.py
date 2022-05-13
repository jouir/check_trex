#!/usr/bin/env python3

import argparse
import logging
import sys

import requests
from nagiosplugin import (
    Check,
    Context,
    Metric,
    Performance,
    Resource,
    ScalarContext,
    Summary,
)
from nagiosplugin.state import Critical, Ok, Unknown, Warn

logger = logging.getLogger(__name__)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        action="store_const",
        const=logging.INFO,
        help="Print more output",
    )
    parser.add_argument(
        "-d",
        "--debug",
        dest="loglevel",
        action="store_const",
        const=logging.DEBUG,
        default=logging.WARNING,
        help="Print even more output",
    )

    parser.add_argument(
        "--version",
        dest="show_version",
        action="store_true",
        help="Print version and exit",
    )

    parser.add_argument(
        "--url",
        dest="url",
        type=str,
        help="API URL of T-Rex miner",
        default="http://127.0.0.1:4067",
    )

    parser.add_argument(
        "--timeout",
        dest="timeout",
        type=int,
        help="Timeout when requesting T-Rex API",
        default=3,
    )

    parser.add_argument(
        "--hashrate-warning",
        dest="hashrate_warning",
        type=int,
        help="Raise warning if hashrate goes below this threshold",
    )
    parser.add_argument(
        "--hashrate-critical",
        dest="hashrate_critical",
        type=int,
        help="Raise critical if hashrate goes below this threshold",
    )
    parser.add_argument(
        "--uptime-warning",
        dest="uptime_warning",
        type=int,
        help="Raise warning if uptime goes below this threshold",
    )
    parser.add_argument(
        "--uptime-critical",
        dest="uptime_critical",
        type=int,
        help="Raise critical if uptime goes below this threshold",
    )
    parser.add_argument(
        "--paused-warning",
        dest="paused_warning",
        action="store_true",
        help="Raise warning when T-Rex is paused",
    )
    parser.add_argument(
        "--paused-critical",
        dest="paused_critical",
        action="store_true",
        help="Raise critical when T-Rex is paused",
    )
    parser.add_argument(
        "--temperature-warning",
        dest="temperature_warning",
        type=int,
        help="Raise warning if temperature goes over this threshold",
        default=70,
    )
    parser.add_argument(
        "--temperature-critical",
        dest="temperature_critical",
        type=int,
        help="Raise critcal if temperature goes over this threshold",
        default=90,
    )
    parser.add_argument(
        "--memory-temperature-warning",
        dest="memory_temperature_warning",
        type=int,
        help="Raise warning if memory temperature goes over this threshold",
        default=90,
    )
    parser.add_argument(
        "--memory-temperature-critical",
        dest="memory_temperature_critical",
        type=int,
        help="Raise critcal if memory temperature goes over this threshold",
        default=110,
    )
    args = parser.parse_args()
    return args


def setup_logging(args):
    logging.basicConfig(format="%(levelname)s: %(message)s", level=args.loglevel)


def show_version():
    print("1.0.0")


class BelowThresholdContext(Context):
    def __init__(self, name, warning=None, critical=None):
        super().__init__(name)
        self.warning = warning
        self.critical = critical

    def evaluate(self, metric, resource):
        if self.critical and metric.value <= self.critical:
            return self.result_cls(Critical, f"{metric.value}<={self.critical}", metric)
        elif self.warning and metric.value <= self.warning:
            return self.result_cls(Warn, f"{metric.value}<={self.warning}", metric)
        else:
            return self.result_cls(Ok, None, metric)

    def performance(self, metric, resource):
        return Performance(
            metric.name,
            metric.value,
            metric.uom,
            self.warning,
            self.critical,
            metric.min,
            metric.max,
        )


class BooleanContext(Context):
    def __init__(self, name, expected=True, warning=False, critical=False):
        super().__init__(name)
        self.expected = expected
        self.warning = warning
        self.critical = critical

    def evaluate(self, metric, resource):
        if not metric.value is self.expected:
            result_type = Ok
            if self.critical:
                result_type = Critical
            elif self.warning:
                result_type = Warn
            return self.result_cls(
                result_type, f"{metric.name} is not {self.expected}", metric
            )
        else:
            return self.result_cls(Ok, None, metric)


class Trex(Resource):
    def __init__(self, url, timeout):
        self.url = url
        self.timeout = timeout

    def probe(self):
        r = requests.get(f"{self.url}/summary", timeout=self.timeout)
        r.raise_for_status()
        data = r.json()

        logger.debug("Response:")
        logger.debug(data)

        metrics = []

        if "hashrate" in data:
            hashrate = data["hashrate"]
            logger.debug(f"Hashrate is {hashrate}")
            metrics.append(Metric("hashrate", hashrate, context="hashrate"))

        if "success" in data:
            success = bool(data["success"])
            if success:
                logger.debug("T-Rex is successfully started")
            else:
                logger.debug("T-Rex is not successfully started")
            metrics.append(Metric("success", success, context="success"))

        if "paused" in data:
            paused = bool(data["paused"])
            if paused:
                logger.debug("T-Rex is paused")
            else:
                logger.debug("T-Rex is not paused")
            metrics.append(Metric("paused", paused, context="paused"))

        if "uptime" in data:
            uptime = data["uptime"]
            seconds = "seconds" if uptime > 1 else "second"
            logger.debug(f"Uptime is {uptime} {seconds}")
            metrics.append(Metric("uptime", uptime, context="uptime"))

        for gpu in data.get("gpus"):
            name = gpu["name"]
            id = gpu["gpu_id"]

            if "temperature" in gpu:
                temperature = gpu["temperature"]
                logger.debug(f"Temperature of {name} ({id}) is {temperature}C")
                metrics.append(
                    Metric("temperature", temperature, context="temperature")
                )

            if "memory_temperature" in gpu:
                temperature = gpu["memory_temperature"]
                logger.debug(
                    f"Memory temperature of {name} ({id}) is {memory_temperature}C"
                )
                metrics.append(
                    Metric(
                        "memory_temperature",
                        memory_temperature,
                        context="memory_temperature",
                    )
                )

        return metrics


class TrexSummary(Summary):
    def problem(self, results):
        return ", ".join(
            [
                f"{result.metric.name} {result.state}: {result.hint}"
                for result in results
                if str(result.state) != "ok"
            ]
        )


def main():
    args = parse_arguments()
    setup_logging(args)

    if args.show_version:
        show_version()
        return

    try:
        check = Check(
            Trex(url=args.url, timeout=args.timeout),
            BooleanContext("success", expected=True),
            BooleanContext(
                "paused",
                expected=True,
                warning=args.paused_warning,
                critical=args.paused_critical,
            ),
            BelowThresholdContext(
                "hashrate",
                warning=args.hashrate_warning,
                critical=args.hashrate_critical,
            ),
            BelowThresholdContext(
                "uptime", warning=args.uptime_warning, critical=args.uptime_critical
            ),
            ScalarContext(
                "temperature",
                warning=args.temperature_warning,
                critical=args.temperature_critical,
            ),
            ScalarContext(
                "memory_temperature",
                warning=args.memory_temperature_warning,
                critical=args.memory_temperature_critical,
            ),
            TrexSummary(),
        )
        check.main()
    except Exception as err:
        print(f"Failed to execute check: {str(err)}")
        logger.debug(err, exc_info=True)
        sys.exit(Unknown.code)


if __name__ == "__main__":
    main()
