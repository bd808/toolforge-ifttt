import argparse
import logging
import sys

import requests


logger = logging.getLogger("test-endpoints")


def test_api(base_url, key):
    headers = {
        "user-agent": "IFTTT endpoint tester",
        "IFTTT-Channel-Key": key or "",
    }
    r = requests.post("{}/v1/test/setup".format(base_url), headers=headers)
    r.raise_for_status()
    setup = r.json()

    for trigger, payload in setup["data"]["samples"]["triggers"].items():
        logger.info("=== {} ===".format(trigger))
        url = "{}/v1/triggers/{}".format(base_url, trigger)
        r = requests.post(url, json={"triggerFields": payload}, headers=headers)
        try:
            r.raise_for_status()
            logger.debug(r.json())
        except requests.exceptions.HTTPError:
            logger.exception("Error from %s", url)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IFTTT endpoint tests")
    parser.add_argument(
        "--url",
        default="https://ifttt.toolforge.org",
        help="Base URL of IFTTT deployment to test.",
    )
    parser.add_argument("--key", help="IFTTT channel key.")
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        dest="loglevel",
        help="Increase logging verbosity.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        stream=sys.stderr,
        format="%(asctime)s %(name)-12s %(levelname)-8s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
        level=max(logging.DEBUG, logging.INFO - (10 * args.loglevel)),
    )
    logging.captureWarnings(True)

    test_api(args.url, args.key)
