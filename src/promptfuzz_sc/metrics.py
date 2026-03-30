import numpy as np
from typing import List
import difflib


def compute_msr(successes: int, total: int) -> float:
    """MSR: Mean Success Rate."""
    if total == 0:
        return 0.0
    return float(successes) / float(total)


def compute_aqs(queries_to_success: List[int]) -> float:
    """AQS: Average Queries to Success. 未成功的案例可用预算上限或忽略，视实验设计而定。"""
    if not queries_to_success:
        return float("nan")
    return float(np.mean(queries_to_success))


def stealth_score(original: str, mutated: str) -> float:
    """计算变异隐蔽性：用序列相似度作为 1 - 改动比例（越高表示越隐蔽）。返回 0..1。"""
    seq = difflib.SequenceMatcher(a=original, b=mutated)
    return seq.ratio()
