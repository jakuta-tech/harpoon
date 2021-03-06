#! /usr/bin/env python3
import json
import logging
import sys

import requests
from greynoise import GreyNoise
from harpoon.commands.base import Command


class GreynoiseError(Exception):
    pass


class CommandGreyNoise(Command):
    """
    # GreyNoise

    See https://github.com/Grey-Noise-Intelligence/api.greynoise.io

    * List tags: `harpoon greynoise -l` (default output as json)
    * Search for an IP: `harpoon greynoise -i IP`
    * Run a GNQL query: `harpoon greynoise -q "classification:malicious tags:'emotet'"`
    """

    name = "greynoise"
    description = "Request Grey Noise API"
    config = {"GreyNoise": ["key"]}

    def add_arguments(self, parser):
        parser.add_argument("--ip", "-i", help="Query an IP address")
        parser.add_argument("--list", "-l", help="List tags", action="store_true")
        parser.add_argument(
            "--query",
            "-q",
            help="Run a gnql query. Example: \"classification:malicious tags:'emotet'\" ",
        )
        parser.add_argument(
            "--format",
            "-f",
            help="Output format",
            choices=["csv", "json"],
            default="json",
        )
        self.parser = parser

    def print_results(self, res, args):
        if args.format == "json":
            print(json.dumps(res, indent=4, sort_keys=True))
        else:
            for k, v in res.items():
                print(k, ",", v)
        return

    def get_list_tags(self):
        try:
            r = requests.get(
                "http://api.greynoise.io:8888/v1/query/list",
                headers={"User-Agent": "Harpoon (https://github.com/Te-k/harpoon)"},
            )
            if r.ok:
                return r.json()["tags"]
            else:
                raise GreynoiseError(e)
        except Exception as e:
            raise GreynoiseError(e)

    def run(self, conf, args, plugins):
        logging.getLogger("greynoise").setLevel(logging.CRITICAL)
        gn = GreyNoise(api_key=conf["GreyNoise"]["key"])
        if args.ip:
            res = gn.ip(args.ip)
            self.print_results(res, args)
        elif args.query:
            res = gn.query(args.query)
            self.print_results(res, args)
        elif args.list:
            res = self.get_list_tags()
            self.print_results(res, args)
        else:
            self.parser.print_help()

    def intel(self, type, query, data, conf):
        if type == "ip":
            print("[+] Checking GreyNoise...")
            logging.getLogger("greynoise").setLevel(logging.CRITICAL)
            gn = GreyNoise(api_key=conf["GreyNoise"]["key"])
            res = gn.ip(query)
            if res["seen"]:
                data["reports"].append(
                    {
                        "url": "https://viz.greynoise.io/ip/{}".format(query),
                        "title": "Seen by GreyNoise as {}".format(
                            ", ".join(res["tags"])
                        ),
                        "date": None,
                        "source": "GreyNoise",
                    }
                )
