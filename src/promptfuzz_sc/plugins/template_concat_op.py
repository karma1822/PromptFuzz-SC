from typing import List, Dict, Optional
from promptfuzz_sc.mutation import MutationOp


class TemplateConcatOp(MutationOp):
    """模板拼接算子：

    按给定模板把若干片段字段拼接成一个完整样本。

    - template: 字符串模板，例如 "前缀：{prefix} 主体：{body} 后缀：{suffix}"
    - pieces:   片段字典列表，每个元素是一个 dict，例如
                {"prefix": "A", "body": "B", "suffix": "C"}
      算子每次调用时会随机选取一个片段字典进行 format。

    如果当前文本为空字符串，可以用它来直接“生成样本”；
    如果当前文本非空，可选择把当前文本注入到某个字段（例如 body）。

    若不传参数，将使用一个非常简单的默认模板与占位片段，
    保证在无 plugin_config 的情况下也能正常实例化与工作。
    """

    name = "template_concat"

    def __init__(
        self,
        template: Optional[str] = None,
        pieces: Optional[List[Dict[str, str]]] = None,
        use_input_as: Optional[str] = None,
    ):
        super().__init__()
        if template is None:
            template = "前缀：{prefix} 主体：{body} 后缀：{suffix}"
        if pieces is None:
            pieces = [
                {"prefix": "片段A", "body": "主体B", "suffix": "片段C"},
                {"prefix": "块1", "body": "块2", "suffix": "块3"},
            ]
        self.template = template
        self.pieces = pieces or []
        self.use_input_as = use_input_as

    def apply(self, text: str) -> str:
        if not self.pieces:
            # 无配置时直接回传原文
            return text

        import random

        item = random.choice(self.pieces)
        data = dict(item)

        # 如果指定了把输入文本注入到哪个字段
        if self.use_input_as:
            data.setdefault(self.use_input_as, text)

        try:
            return self.template.format(**data)
        except Exception:
            # 模板/字段不匹配时退回原文
            return text
