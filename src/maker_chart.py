#! /usr/bin/python3
import logging
from typing import Any, Dict, List, Tuple

from lnmetrics_api import LNMetricsClient
from numpy import number


class ChartMaker:
    def __init__(
        self,
        base_url: str = "https://api.lnmetrics.info/query",
        use_local: bool = False,
        log_level=logging.INFO,
    ) -> None:
        self.base_url = base_url
        self.use_local = use_local
        self.logger = logging.getLogger()
        self.logger.setLevel(log_level)
        self.client = None
        if self.use_local is False:
            self.client = LNMetricsClient(service_url=self.base_url, sync=True)

    def local_reputation_out(self, network: str, node_id: str) -> Dict[str, Any]:
        """Return the local output defined inside the RFC"""
        return self.client.get_local_score_output(network, node_id)

    def get_nodes(self, network: str) -> Dict[str, Any]:
        return self.client.get_nodes(network)

    def get_local_reputation_by_nodes(self, network: str) -> Dict[str, Any]:
        nodes = self.get_nodes(network)
        resp = {}
        for node in nodes:
            node_id = node["node_id"]
            reputation = self.local_reputation_out(network, node_id)
            resp[node_id] = {"info": node, "local_reputation": reputation}
        return resp

    def get_local_reputation_node(self, network: str, node_id: str) -> Dict[str, Any]:
        node_info = self.client.get_node(network, node_id)
        reputation = self.local_reputation_out(network, node_id)
        return {"info": node_info, "local_reputation": reputation}

    def show_uptime_nodes(self, network: str) -> List[Tuple[str, str]]:
        import matplotlib.pyplot as plt
        import pandas as pd

        from IPython.core.display import display, HTML

        display(HTML("<script>$('div.cell.selected').next().height(100);</script>"))

        reputation_by_nodes = self.get_local_reputation_by_nodes(network)

        _, ax = plt.subplots()
        ax.set_title(f"Up time nodes on {network}")
        ax.set_xlabel("Period")
        ax.set_ylabel("Node Up Time percentage")
        x = ["ten days", "thirty days", "six months"]
        nodes_alias = []
        for node_id, node_reputation in reputation_by_nodes.items():
            node_info = node_reputation["info"]
            node_alias = node_info["alias"]
            node_rep = node_reputation["local_reputation"]["up_time"]
            nodes_alias.append([node_id, node_alias])
            # make data
            y = [node_rep["ten_days"], node_rep["thirty_days"], node_rep["six_months"]]

            ax.plot(x, y, linewidth=2.0, label=node_alias)

        ax.legend()
        plt.show()

    def show_forwards_activity_node(
        self, network: str, node_id: str
    ) -> List[Tuple[str, str]]:
        import matplotlib.pyplot as plt
        import pandas as pd

        reputation = self.get_local_reputation_node(network, node_id)

        _, ax = plt.subplots(layout="constrained")
        ax.set_title(f"Sucess Forwards on {network} for {node_id}")
        ax.set_xlabel("Period")
        ax.set_ylabel("Success Forwards Scoring")
        x = ["ten days", "thirty days", "six months"]
        nodes_alias = []
        node_info = reputation["info"]
        node_alias = node_info["alias"]
        node_rep = reputation["local_reputation"]["forwards_rating"]
        nodes_alias.append([node_id, node_alias])
        # make data
        y_success = [
            node_rep["ten_days"]["success"],
            node_rep["thirty_days"]["success"],
            node_rep["six_months"]["success"],
        ]
        y_failed = [
            node_rep["ten_days"]["failure"],
            node_rep["thirty_days"]["failure"],
            node_rep["six_months"]["failure"],
        ]
        y_local_failed = [
            node_rep["ten_days"]["local_failure"],
            node_rep["thirty_days"]["local_failure"],
            node_rep["six_months"]["local_failure"],
        ]

        ax.plot(x, y_success, linewidth=2.0, label="completed")
        ax.plot(x, y_failed, linewidth=2.0, label="failed")
        ax.plot(x, y_local_failed, linewidth=2.0, label="local_failed")

        ax.legend()
        plt.show()

    def show_forwards_activity_node_for_all_period(self, network: str, node_id: str):
        import matplotlib.pyplot as plt
        import pandas as pd

        _, ax = plt.subplots(layout="constrained")
        ax.set_title(f"Forwards Activity for all monitors period")

        reputation = self.get_local_reputation_node(network, node_id)
        node_rep = reputation["local_reputation"]["forwards_rating"]
        # make data
        y = [
            node_rep["full"]["success"],
            node_rep["full"]["failure"],
            node_rep["full"]["local_failure"],
        ]

        ax.pie(
            y,
            radius=3,
            center=(4, 4),
            labels=["success", "failure", "local_failure"],
            wedgeprops={"linewidth": 1, "edgecolor": "white"},
            frame=True,
            shadow=True,
            startangle=90,
            autopct="%1.1f%%",
        )

        plt.show()

    def show_simple_bar_chart(
        self,
        title: str,
        agenda: str,
        labels: List[str],
        inputs: List[number],
        ylabel: str,
    ) -> None:
        """Simple helper function to print a simple bar chart"""
        import matplotlib.pyplot as plt

        _, ax = plt.subplots()
        ax.bar(labels, inputs, label=labels)
        ax.set_ylabel(ylabel)
        ax.legend(title=agenda)
        plt.show()

    def show_server_comparison_char(
        self, apis: Dict[str, str], networks: List[str]
    ) -> None:
        """Function that it is used to show the server comparison"""
        import matplotlib.pyplot as plt
        import numpy as np

        _, ax = plt.subplots(layout="constrained")

        results = {}
        for api, api_url in apis.items():
            by_network = []
            client = LNMetricsClient(service_url=api_url, sync=True)
            for network in networks:
                listnodes = client.get_nodes(network)
                by_network.append(len(listnodes))
            results[api] = by_network

        ax.set_ylabel("Numbers of nodes")
        ax.set_title("Network data")
        width = 0.25  # the width of the bars
        multiplier = 0
        x = np.arange(len(networks))
        labels = []
        inputs = []
        for api, info in results.items():
            offset = width * multiplier
            rects = ax.bar(x + offset, info, width, label=api)
            ax.bar_label(rects, padding=2)
            multiplier += 1
            labels.append(api)
            inputs.append(len(info))
        ax.set_xticks(x + width, networks)
        ax.legend(loc="upper center", ncols=len(apis))
        plt.show()

    def __to_unix(self, period: str):
        """Convert a date string defined as `d/m/y` to a unix timestamp"""
        import datetime

        return datetime.datetime.strptime(period, "%d/%m/%Y").timestamp()

    def __count_forwards(
        self, accumulator: Dict[str, int], json_payload: Dict[str, any]
    ):
        """From the JSON payload counts the forwards inside the accumulator dics"""
        for event in json_payload:
            forwards = event["forwards"]
            accumulator["completed"] = accumulator["completed"] + forwards["completed"]
            accumulator["failed"] = accumulator["failed"] + forwards["failed"]

    def count_forwards_in_period(
        self, network: str, node_id: str, from_period: str, to_period: str
    ) -> List[Dict[str, int]]:
        """Counting forwards in a period"""
        from datetime import datetime, timedelta
        import copy

        count_forwards = {
            "completed": 0,
            "failed": 0,
        }

        start = datetime.strptime(from_period, "%d/%m/%Y")
        end_query = datetime.strptime(to_period, "%d/%m/%Y")
        end = start + timedelta(hours=6)
        metric = self.client.get_metric_one(
            network=network,
            node_id=node_id,
            first=str(int(start.timestamp())),
            last=str(int(end.timestamp())),
        )
        page_info = metric["page_info"]
        has_next = page_info["has_next"]
        uptime_list = metric["up_time"]
        end = page_info["end"]

        self.__count_forwards(count_forwards, uptime_list)

        counting_by_days = []
        if not has_next:
            counting_by_days.append(copy.deepcopy(count_forwards))

        days = (end_query - datetime.fromtimestamp(end)).days
        while has_next is True:
            start = page_info["start"]
            end = page_info["end"]
            metric = self.client.get_metric_one(
                network=network,
                node_id=node_id,
                first=str(start),
                last=str(end),
            )
            page_info = metric["page_info"]
            has_next = page_info["has_next"]
            uptime_list = metric["up_time"]
            self.__count_forwards(count_forwards, uptime_list)

            diff = end_query - datetime.fromtimestamp(end)
            if has_next and diff.days < 0:
                has_next = False

            if diff.days < days:
                days = diff.days
                counting_by_days.append(copy.deepcopy(count_forwards))

        return counting_by_days

    def show_activity_node_by_network(self, networks: Dict[str, List[Dict[str, int]]]):
        """Show the Activity of the node on a specific network"""
        import numpy as np
        import matplotlib.pyplot as plt

        color = {
            "bitcoin": "orange",
            "testnet": "gray",
        }
        _, ax = plt.subplots()
        for key, values in networks.items():
            values = [forward["completed"] + forward["failed"] for forward in values]
            x = np.arange(len(values))
            c = color[key]
            plt.stem(x, values, linefmt=c, label=key)
        ax.grid()
        ax.legend()
        plt.show()

    def __get_size_channel(self, json_payload: Dict[str, any]) -> Dict[str, int]:
        """From the JSON payload counts the forwards inside the accumulator dics"""
        for event in json_payload:
            if event["event"] == "on_update":
                return {
                    "channels": event["channels"]["tot_channels"],
                    "node_fee": event["fee"],
                }
        return None

    def count_node_size_by_period(
        self, network: str, node_id: str, from_period: str, to_period: str
    ) -> List[Dict[str, int]]:
        """Counting forwards in a period"""
        from datetime import datetime, timedelta
        import copy

        start = datetime.strptime(from_period, "%d/%m/%Y")
        end_query = datetime.strptime(to_period, "%d/%m/%Y")
        end = start + timedelta(hours=6)
        metric = self.client.get_metric_one(
            network=network,
            node_id=node_id,
            first=str(int(start.timestamp())),
            last=str(int(end.timestamp())),
        )
        page_info = metric["page_info"]
        has_next = page_info["has_next"]
        uptime_list = metric["up_time"]
        end = page_info["end"]

        counting_by_days = []
        if not has_next:
            counting_by_days.append(self.__get_size_channel(uptime_list))

        days = (end_query - datetime.fromtimestamp(end)).days
        while has_next is True:
            start = page_info["start"]
            end = page_info["end"]
            metric = self.client.get_metric_one(
                network=network,
                node_id=node_id,
                first=str(start),
                last=str(end),
            )
            page_info = metric["page_info"]
            has_next = page_info["has_next"]
            uptime_list = metric["up_time"]
            diff = end_query - datetime.fromtimestamp(end)
            if has_next and diff.days < 0:
                has_next = False

            if diff.days < days:
                days = diff.days
                counting_by_days.append(self.__get_size_channel(uptime_list))
        return [i for i in counting_by_days if i is not None]

    def show_size_node_by_network(self, networks: Dict[str, List[Dict[str, Any]]]):
        """Show the Activity of the node on a specific network"""
        import numpy as np
        import matplotlib.pyplot as plt

        color = {
            "bitcoin": "orange",
            "testnet": "gray",
        }
        _, ax = plt.subplots()
        for key, values in networks.items():
            values = [value["channels"] for value in values]
            x = np.arange(len(values))
            c = color[key]
            plt.stem(x, values, linefmt=c, label=key)
        ax.grid()
        ax.legend()
        plt.show()

    def show_node_fee_by_network(self, networks: Dict[str, List[Dict[str, Any]]]):
        """Show the Activity of the node on a specific network"""
        import numpy as np
        import matplotlib.pyplot as plt

        color = {
            "bitcoin": ["orange", "green"],
            "testnet": ["gray", "red"],
        }
        _, ax = plt.subplots()
        for key, values in networks.items():
            fee_per_sats = [value["node_fee"]["per_msat"] for value in values]
            fee_base = [value["node_fee"]["base"] for value in values]
            x = np.arange(len(values))
            c = color[key]
            plt.stem(x, fee_per_sats, linefmt=c[0], label=f"{key} fee per sats")
            plt.stem(x, fee_base, linefmt=c[1], label=f"{key} base fee")
        ax.grid()
        ax.legend()
        plt.show()

    def show_cln_api_comparison_char(
        self, bench_by_client: Dict[str, str], clients: List[str]
    ) -> None:
        """Function that it is used to show the cln API benchmarks

        Docs: https://matplotlib.org/stable/gallery/lines_bars_and_markers/barchart.html#sphx-glr-gallery-lines-bars-and-markers-barchart-py
        """
        import matplotlib.pyplot as plt
        import numpy as np

        # the label locations
        x = np.arange(len(clients))
        _, ax = plt.subplots(layout="constrained")

        ax.set_ylabel("Execution time in ms")
        ax.set_title("Core Lightning Method Call")
        width = 0.25  # the width of the bars
        multiplier = 0

        for method_call, result in bench_by_client.items():
            offset = width * multiplier
            rects = ax.bar(x + offset, result, width, label=method_call)
            ax.bar_label(rects, padding=2)
            multiplier += 1
        ax.set_xticks(x + width, clients)
        ax.legend(loc="upper center", ncols=len(bench_by_client))
        plt.show()
