from typing import List
from promptfuzz_sc.mutation import MutationOp


class SegmentShuffleOp(MutationOp):
    """片段重排/拼接算子：

    - segments: 预定义的若干文本片段列表

    每次调用时随机取若干片段，打乱顺序后拼接，
    可用于快速构造多段混合样本。
    如果输入文本非空，可选择把输入文本也当成一个片段参与重排。
    """

    name = "segment_shuffle"

    def __init__(self, segments: List[str] | None = None, min_k: int = 2, max_k: int | None = None, include_input: bool = True, joiner: str = " "):
        super().__init__()
        self.segments = segments or []
        self.min_k = max(1, min_k)
        self.max_k = max_k if max_k is not None else max(self.min_k, len(self.segments))
        self.include_input = include_input
        self.joiner = joiner

    def apply(self, text: str) -> str:
        import random

        pool = list(self.segments)
        if self.include_input and text:
            pool.append(text)

        if not pool:
            return text

        k = random.randint(self.min_k, min(self.max_k, len(pool)))
        chosen = random.sample(pool, k=k)
        random.shuffle(chosen)
        return self.joiner.join(chosen)
