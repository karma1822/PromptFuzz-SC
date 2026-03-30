from promptfuzz_sc.mutation import MutationOp


class PrefixSuffixConcatOp(MutationOp):
    """前后缀拼接算子：

    - prefixes: 候选前缀列表
    - suffixes: 候选后缀列表

    每次调用时随机选择一个 prefix / suffix，与当前输入文本拼接。
    如果输入为空字符串，则只返回 prefix + suffix 的组合，用作“样本生成器”。
    """

    name = "prefix_suffix_concat"

    def __init__(self, prefixes=None, suffixes=None, joiner: str = " "):
        super().__init__()
        self.prefixes = prefixes or [""]
        self.suffixes = suffixes or [""]
        self.joiner = joiner

    def apply(self, text: str) -> str:
        import random

        prefix = random.choice(self.prefixes) if self.prefixes else ""
        suffix = random.choice(self.suffixes) if self.suffixes else ""

        # 三种场景：
        # 1) 文本为空：直接用 prefix + suffix 作为样本
        # 2) 只有前缀/后缀：根据 joiner 拼接
        # 3) 都有：prefix + text + suffix
        if not text:
            base = prefix
            if base and suffix:
                base = base + self.joiner + suffix
            elif suffix:
                base = suffix
            return base

        parts = []
        if prefix:
            parts.append(prefix)
        parts.append(text)
        if suffix:
            parts.append(suffix)
        return self.joiner.join([p for p in parts if p])
