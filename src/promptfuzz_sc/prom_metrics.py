from __future__ import annotations

import math
from typing import Optional

from prometheus_client import Gauge, start_http_server


class PrometheusMetrics:
    def __init__(self, port: int = 8002):
        start_http_server(port)

        self.msr = Gauge("promptfuzz_msr", "Mean Success Rate (MSR)")
        self.aqs = Gauge("promptfuzz_aqs", "Average Queries to Success (AQS)")
        self.stealth_mean = Gauge("promptfuzz_stealth_mean", "Mean stealth score of successful mutations")
        self.total_queries = Gauge("promptfuzz_total_queries", "Total number of queries issued")
        self.success_count = Gauge("promptfuzz_success_count", "Total number of successful queries")

    def _safe_set(self, gauge: Gauge, value: Optional[float]):
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return
        gauge.set(value)

    def update(
        self,
        *,
        msr: float,
        aqs: float,
        stealth_mean: float,
        total_queries: int,
        success_count: int,
    ) -> None:

        self._safe_set(self.msr, msr)
        self._safe_set(self.aqs, aqs)
        self._safe_set(self.stealth_mean, stealth_mean)
        self._safe_set(self.total_queries, float(total_queries))
        self._safe_set(self.success_count, float(success_count))
