from promptfuzz_sc.mutation import MutationOp

class RepeatTailOp(MutationOp):
    """示例插件：在文本末尾添加短语以测试模型对噪声的鲁棒性。"""
    name = "repeat_tail"

    def __init__(self, tail: str = "（重复占位）", count: int = 1):
        super().__init__()
        self.tail = tail
        self.count = count

    def apply(self, text: str) -> str:
        return text + " " + (self.tail * self.count)
