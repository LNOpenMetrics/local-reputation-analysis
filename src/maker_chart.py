#! /usr/bin/python3
import logging
import json
import random
from os import path
from datetime import datetime
from pyecharts.charts import Bar, HeatMap
from pyecharts.faker import Faker


class ChartMaker:
    def __init__(
        self,
        base_dir: str = "../resources",
        log_level=logging.INFO,
    ) -> None:
        self.base_dir = base_dir
        self.logger = logging.getLogger()
        self.logger.setLevel(log_level)

    def make_node_status(self, node_id: str) -> Bar:
        node_dir = "{}/{}".format(self.base_dir, node_id)
        self.logger.debug("Node path: {}".format(node_dir))
        if not path.exists(node_dir):
            raise Exception("Path {} not exist".format(path))
        with open("{}/getinfo.json".format(node_dir)) as info_file:
            json_info = json.load(info_file)
            self.logger.debug("Get info node with id: {}".format(node_id))
            self.logger.debug(json_info)
            assert json_info["id"] == node_id

        node_with_channel = []
        # Contributions days in str format
        contribution_days = []
        with open("{}/metric_one.json".format(node_dir)) as metric_one_file:
            json_metric_one = json.load(metric_one_file)
            up_time_days = json_metric_one["up_time"]

            days = {}
            for up_time in up_time_days:
                if "stop" in up_time["event"]:
                    status = 0
                else:
                    status = 1
                date = datetime.fromtimestamp(up_time["timestamp"])
                date_str = date.strftime("%Y-%m-%d")

                if date_str not in days:
                    days[date_str] = {"count": 0, "events": []}
                days[date_str] = {
                    "timestamp": up_time["timestamp"],
                    "value": status,
                    "events": days[date_str]["events"] + [up_time["event"]],
                    "count": days[date_str]["count"] + 1,
                    "week_day": date.weekday(),
                }

        days_label = []
        days_value = []
        on_close = []
        on_start = []
        on_update = []
        unknown = []
        for key, value in days.items():
            days_label.append(key)
            days_value.append(value["count"])
            update = ChartMaker.__filter_uptime_by_event(value["events"], "on_update")
            on_update.append(len(update))
            close = ChartMaker.__filter_uptime_by_event(value["events"], "on_close")
            on_close.append(len(close))
            start = ChartMaker.__filter_uptime_by_event(value["events"], "on_start")
            on_start.append(len(start))
            unknown_fil = ChartMaker.__filter_uptime_by_event(value["events"], "")
            unknown.append(len(unknown_fil))

        bar = Bar()
        bar.add_xaxis(days_label).add_yaxis("Update", on_update).add_yaxis(
            "Closed", on_close
        ).add_yaxis(
            "Started", on_start
        ).add_yaxis(
            "Unknown", unknown
        ).set_series_opts(
            stack="MY_STACK_NAME"
        )
        return bar

    def make_payments_analysis_by_node(self, node_id: str) -> Bar:
        node_dir = "{}/{}".format(self.base_dir, node_id)
        self.logger.debug("Node path: {}".format(node_dir))
        if not path.exists(node_dir):
            raise Exception("Path {} not exist".format(path))
        with open("{}/getinfo.json".format(node_dir)) as info_file:
            json_info = json.load(info_file)
            self.logger.debug("Get info node with id: {}".format(node_id))
            self.logger.debug(json_info)
            assert json_info["id"] == node_id

        node_with_channel = []

        with open("{}/metric_one.json".format(node_dir)) as metric_one_file:
            json_metric_one = json.load(metric_one_file)
            self.logger.debug("Metric One with node id: {}".format(node_id))
            self.logger.debug(json_metric_one)
            channels_info = json_metric_one["channels_info"]
            # TODO: This is an ack to work around into this
            # https://github.com/OpenLNMetrics/go-metrics-reported/issues/21
            map = dict()
            for channel_info in channels_info:
                if channel_info["forwords"] is None:
                    continue
                payments_failed = []
                payment_local_failed = []
                payments_success = []
                # TODO: Typo mistake, forwords instead of forwards
                failed_payments = ChartMaker.__filter_payment_by_status(
                    channel_info["forwords"], "failed"
                )
                payments_failed.append(len(failed_payments))
                local_failed_payments = ChartMaker.__filter_payment_by_status(
                    channel_info["forwords"], "local_failed"
                )
                payment_local_failed.append(len(local_failed_payments))
                success_payments = ChartMaker.__filter_payment_by_status(
                    channel_info["forwords"], "settled"
                )
                payments_success.append(len(success_payments))
                map[channel_info["node_alias"]] = {
                    "success": payments_success,
                    "failed": payments_failed,
                    "local_failed": payment_local_failed,
                }
        payments_failed = []
        payment_local_failed = []
        payments_success = []
        for key, value in map.items():
            node_with_channel.append(key)
            payments_failed += value["failed"]
            payment_local_failed += value["local_failed"]
            payments_success += value["success"]
        bar = Bar()
        bar.add_xaxis(node_with_channel).add_yaxis(
            "settled", payments_success
        ).add_yaxis("failed", payments_failed).add_yaxis(
            "local_failed", payment_local_failed
        )
        return bar

    @staticmethod
    def __filter_payment_by_status(payments: list, status: str) -> list:
        """
        Apply the filter by status on a list of payments.

        :param payments: List of forwards payments
        :param status: Status where the list need to be filtered
        :return: A new list with only payment with the specified status
        """
        if payments is None:
            return []
        return list(filter(lambda payment: payment["status"] == status, payments))

    @staticmethod
    def __filter_uptime_by_event(events: list, pivot: str) -> list:
        if events is None:
            return []
        return list(filter(lambda event: event == pivot, events))

    def make_payment_by_node(self, node_id: str):
        pass

    def make_capacity_channel(self, node_id: str):
        pass
