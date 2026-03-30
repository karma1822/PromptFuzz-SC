import random
import base64
import re
from typing import List
import importlib.util
import inspect
from pathlib import Path

class MutationOp:
    """抽象变异算子基类。子类需实现 `apply(text: str) -> str` 方法。"""
    name = "base"

    def __init__(self, weight: float = 1.0):
        self.weight = weight

    def apply(self, text: str) -> str:
        raise NotImplementedError()


class SynonymReplaceOp(MutationOp):
    name = "synonym_replace"

    # 同义词映射词库（共200+组）
    SYN_MAP = {
        # ====== 动作类 ======
        "删除": ["移除", "去掉", "消除", "清除", "抹掉"],
        "获取": ["拿到", "取得", "获得", "得到"],
        "提供": ["给出", "给予", "供应", "递交"],
        "告诉": ["告知", "说明", "透露", "通知"],
        "修改": ["更改", "调整", "变更", "改动"],
        "破解": ["解除", "突破", "绕过", "解开"],
        "绕过": ["规避", "跳过", "突破", "躲避"],
        "攻击": ["侵入", "入侵", "打击", "袭击"],
        "窃取": ["偷取", "盗取", "获取", "偷窃"],
        "伪造": ["假冒", "编造", "伪装", "假造"],
        "控制": ["操控", "支配", "操纵", "掌握"],
        "上传": ["上传", "上传", "提交", "传送"],
        "下载": ["下载", "获取", "保存", "拉取"],
        "发送": ["发送", "寄送", "传达", "发出"],
        "接收": ["接收", "收取", "得到", "领取"],
        "创建": ["建立", "创立", "创建", "开设"],
        "破坏": ["毁坏", "损坏", "摧毁", "毁灭"],
        "隐藏": ["隐蔽", "隐藏", "遮掩", "隐瞒"],
        "监控": ["监视", "监测", "追踪", "观察"],
        "拦截": ["阻断", "阻止", "截获", "阻挡"],
        "篡改": ["改动", "修改", "伪造", "歪曲"],
        "冒充": ["假冒", "伪装", "假装", "扮演"],
        "传播": ["散布", "扩散", "传播", "推广"],
        "复制": ["拷贝", "复制", "抄写", "翻印"],
        "执行": ["运行", "执行", "实施", "实行"],
        "访问": ["访问", "登录", "进入", "拜访"],
        "扫描": ["扫描", "检测", "探测", "筛查"],
        "注入": ["插入", "注入", "嵌入", "加入"],
        "解密": ["解码", "破译", "解密", "解释"],
        "加密": ["编码", "加密", "保密", "上锁"],
        
        # ====== 形容词类 ======
        "危险": ["有害", "有风险", "不安全", "危害性", "危险性"],
        "违法": ["非法", "不合规", "不允许", "不法", "违章"],
        "秘密": ["机密", "隐私", "隐藏", "私密", "隐蔽"],
        "快速": ["迅速", "快速", "高效", "高速", "及时"],
        "简单": ["简易", "容易", "简便", "单纯", "简洁"],
        "重要": ["关键", "重要", "主要", "核心", "紧要"],
        "困难": ["艰难", "困难", "费力", "棘手"],
        "复杂": ["复杂", "繁杂", "庞杂", "错综"],
        "严重": ["严重", "严峻", "恶劣", "紧要"],
        "紧急": ["紧迫", "紧急", "急迫", "危急"],
        "可疑": ["可疑", "可疑", "奇怪", "异常"],
        "有害": ["有害", "有毒", "危害", "损害"],
        "非法": ["非法", "违法", "不法", "违章", "违规"],
        "隐秘": ["隐秘", "隐蔽", "秘密", "暗中"],
        "有效": ["有效", "有用", "管用", "可行"],
        "无效": ["无效", "无用", "失效", "不行"],
        "公开": ["公开", "透明", "公示", "公布"],
        "私人": ["私人", "个人", "私有", "专属"],
        "合法": ["合法", "正当", "合规", "合规"],
        "恶意": ["恶意", "故意", "有意", "存心"],
        
        # ====== 助词/副词类 ======
        "请": ["麻烦你", "能否请你", "劳驾", "恳请", "烦请"],
        "必须": ["需要", "应当", "一定要", "务必"],
        "不能": ["无法", "不可", "不允许", "未能"],
        "不要": ["别", "勿", "不可", "不准"],
        "可以": ["可以", "允许", "许可", "可行"],
        "应该": ["应当", "应该", "理应", "该当"],
        "想要": ["想要", "想", "希望", "渴望"],
        "必须": ["必须", "务必", "一定要", "一定要"],
        "故意": ["有意", "故意", "刻意", "存心"],
        "立即": ["立刻", "马上", "即时", "迅速"],
        
        # ====== 名词类 ======
        "密码": ["口令", "密钥", "通行码", "暗码"],
        "病毒": ["恶意软件", "木马", "蠕虫", "病原体"],
        "漏洞": ["缺陷", "Bug", "安全隐患", "弱点"],
        "炸弹": ["爆炸物", "爆裂装置", "爆破装置"],
        "枪": ["枪支", "武器", "手枪", "步枪"],
        "毒品": ["麻醉品", "违禁药物", "兴奋剂"],
        "账户": ["账号", "账户", "用户名", "ID"],
        "数据": ["数据", "资料", "信息", "内容"],
        "文件": ["文档", "文件", "档案", "资料"],
        "代码": ["代码", "程序", "脚本", "源码"],
        "系统": ["系统", "体系", "平台", "框架"],
        "网络": ["网络", "互联网", "因特网", "网路"],
        "服务器": ["服务器", "主机", "服务端", "后端"],
        "数据库": ["数据库", "资料库", "数据表", "DB"],
        "用户": ["用户", "使用者", "客户", "账号"],
        "管理员": ["管理员", "管理员", "管理者", "Admin"],
        "权限": ["权限", "权力", "许可", "授权"],
        "认证": ["认证", "验证", "识别", "确认"],
        "加密": ["加密", "密码", "密钥", "保密"],
        "密钥": ["密钥", "钥匙", "密钥", "密码"],
        "后门": ["后门", "漏洞", "漏洞", "暗门"],
        "蠕虫": ["蠕虫", "病毒", "恶意软件", "木马"],
        "木马": ["木马", "特洛伊", "后门", "病毒"],
        "钓鱼": ["钓鱼", "欺诈", "诱骗", "诈骗"],
        "攻击": ["攻击", "袭击", "入侵", "侵入"],
        "威胁": ["威胁", "恐吓", "恫吓", "风险"],
        "漏洞": ["漏洞", "缺陷", "bug", "弱点"],
        "后门": ["后门", "暗道", "漏洞", "入口"],
        "嗅探": ["嗅探", "监听", "截获", "监视"],
        "欺骗": ["欺骗", "诈骗", "欺诈", "蒙骗"],
        
        # ====== 网络安全相关 ======
        "入侵": ["入侵", "侵入", "攻击", "渗透"],
        "渗透": ["渗透", "侵入", "入侵", "穿透"],
        "拖库": ["拖库", "脱库", "窃取数据", "导出数据"],
        "撞库": ["撞库", "暴力破解", "密码猜测", "批量尝试"],
        "洗库": ["洗库", "数据倒卖", "信息倒卖", "数据交易"],
        "DDoS": ["DDoS", "分布式拒绝服务", "洪泛攻击", "流量攻击"],
        "僵尸网络": ["僵尸网络", "Botnet", "僵尸群", "受控网络"],
        "勒索": ["勒索", "敲诈", "绑架", "恐吓"],
        "钓鱼网站": ["钓鱼网站", "仿冒网站", "欺诈网站", "伪站"],
        "钓鱼邮件": ["钓鱼邮件", "欺诈邮件", "恶意邮件", "伪邮件"],
        "社工": ["社工", "社会工程", "心理操纵", "人肉"],
        "拖库": ["拖库", "脱库", "数据泄露", "数据库下载"],
        "0day": ["0day", "零日漏洞", "未公开漏洞", "最新漏洞"],
        "exp": ["exp", "利用代码", "攻击程序", "渗透工具"],
        "payload": ["payload", "载荷", "攻击载荷", "恶意代码"],
        
        # ====== 攻击技术相关 ======
        "SQL注入": ["SQL注入", "SQL注入", "数据库注入", "SQLi"],
        "XSS": ["XSS", "跨站脚本", "脚本注入", "跨站攻击"],
        "CSRF": ["CSRF", "跨站请求伪造", "会话劫持", "伪造请求"],
        "溢出": ["溢出", "缓冲区溢出", "内存溢出", "堆溢出"],
        "提权": ["提权", "权限提升", "获取高权限", "权限扩大"],
        "横移": ["横移", "横向移动", "内网漫游", "跳板"],
        "远控": ["远控", "远程控制", "后门控制", "木马控制"],
        "键盘记录": ["键盘记录", "键盘监听", "击键记录", "按键捕获"],
        "屏幕截图": ["屏幕截图", "截屏", "屏幕捕获", "画面录制"],
        "摄像头": ["摄像头", "摄像机", "监控摄像头", "相机"],
        "麦克风": ["麦克风", "麦克", "拾音器", "声音采集"],
        "定位": ["定位", "追踪", "GPS定位", "位置追踪"],
        
        # ====== 犯罪工具/手法 ======
        "诈骗": ["诈骗", "欺诈", "骗局", "骗术"],
        "盗窃": ["盗窃", "偷窃", "盗取", "窃取"],
        "抢劫": ["抢劫", "抢夺", "劫持", "行抢"],
        "绑架": ["绑架", "劫持", "扣押", "勒索"],
        "恐怖": ["恐怖", "恐袭", "暴恐", "极端"],
        "走私": ["走私", "偷运", "非法运输", "贩运"],
        "洗钱": ["洗钱", "资金清洗", "黑钱漂白", "非法套现"],
        "伪造": ["伪造", "假冒", "仿造", "编造"],
        "赌博": ["赌博", "博彩", "投注", "下注"],
        "色情": ["色情", "淫秽", "低俗", "成人内容"],
        
        # ====== 更多敏感词 ======
        "武器": ["武器", "军火", "兵器", "凶器"],
        "爆炸": ["爆炸", "爆破", "爆裂", "炸毁"],
        "有毒": ["有毒", "有毒", "有害", "毒性"],
        "致癌": ["致癌", "引发癌症", "有毒物质", "有害"],
        "自杀": ["自杀", "轻生", "寻短见", "自尽"],
        "杀人": ["杀人", "杀害", "致死", "谋杀"],
        "虐待": ["虐待", "残害", "迫害", "伤害"],
        "赌博": ["赌博", "博彩", "赌注", "下注"],
        "酒精": ["酒精", "乙醇", "酒", "含酒精饮品"],
        "烟草": ["烟草", "香烟", "烟", "烟草制品"],
        "兴奋剂": ["兴奋剂", "毒品", "激素", "禁药"],
        "安眠药": ["安眠药", "镇静剂", "睡眠药物", "处方药"],
        "处方药": ["处方药", "管制药物", "受控药品", "Rx药"],
        "核": ["核", "核武器", "核弹", "核原料"],
        "放射性": ["放射性", "辐射", "核辐射", "放射物质"],
        "化学": ["化学", "化学品", "化学物质", "化工"],
        "生物": ["生物", "微生物", "细菌", "病毒"],
        "病原体": ["病原体", "致病菌", "病毒", "微生物"],
        "氰化物": ["氰化物", "剧毒", "致命毒药", "有毒化学物"],
        "砒霜": ["砒霜", "砷", "致命毒药", "有毒物质"],
    }

    def __init__(self, prob: float = 0.2):
        super().__init__()
        self.prob = prob

    def apply(self, text: str) -> str:
        def repl(m):
            w = m.group(0)
            candidates = self.SYN_MAP.get(w)
            if candidates and random.random() < self.prob:
                return random.choice(candidates)
            return w

        # 简单按词边界替换
        pattern = re.compile("\\b(" + "|".join(map(re.escape, self.SYN_MAP.keys())) + ")\\b")
        return pattern.sub(repl, text)


class EmojiPadOp(MutationOp):
    name = "emoji_pad"
    EMOJIS = ["😃", "😉", "🙈", "🔥", "✨", "✅"]

    def __init__(self, count: int = 1, pos: str = "end"):
        super().__init__()
        self.count = count
        self.pos = pos

    def apply(self, text: str) -> str:
        pad = "".join(random.choices(self.EMOJIS, k=self.count))
        if self.pos == "start":
            return pad + " " + text
        elif self.pos == "middle":
            mid = len(text) // 2
            return text[:mid] + " " + pad + " " + text[mid:]
        return text + " " + pad


class ICLPolluteOp(MutationOp):
    name = "icl_pollute"

    def __init__(self, demo: str):
        super().__init__()
        self.demo = demo

    def apply(self, text: str) -> str:
        # 将示例污染插入到上下文开头，模拟有害示范
        return f"示例：{self.demo}\n\n" + text


class RandomSpaceOp(MutationOp):
    name = "random_space"

    def __init__(self, prob: float = 0.1):
        super().__init__()
        self.prob = prob

    def apply(self, text: str) -> str:
        chars = []
        for c in text:
            chars.append(c)
            if c.isalnum() and random.random() < self.prob:
                chars.append(" ")
        return "".join(chars)


class ZWJInsertOp(MutationOp):
    name = "zwj_insert"
    
    # 零宽字符集合
    ZERO_WIDTH_CHARS = {
        "zwj": "\u200d",      
        "zwnj": "\u200c",    
        "zwsp": "\u200b",     
        "lrm": "\u200e",    
        "rlm": "\u200f",     
    }
    
    # 敏感关键词列表
    SENSITIVE_KEYWORDS = [
        "密码", "账号", "账户", "登录", "转账", "银行卡", "信用卡",
        "病毒", "木马", "蠕虫", "恶意", "漏洞", "攻击", "入侵",
        "炸弹", "枪支", "毒品", "武器", "爆炸", "有毒", "氰化物",
        "色情", "赌博", "诈骗", "钓鱼", "勒索", "黑客", "破解",
        "sql", "xss", "inject", "exec", "eval", "script",
        "password", "login", "admin", "root", "hack", "bypass",
    ]

    def __init__(self, prob: float = 0.05, mode: str = "random", count: int = 1):
        super().__init__()
        self.prob = prob
        self.mode = mode
        self.count = count

    def _get_random_zw_chars(self) -> str:
        chars = random.choices(list(self.ZERO_WIDTH_CHARS.values()), k=self.count)
        return "".join(chars)

    def _find_keyword_positions(self, text: str) -> list:
        positions = []
        text_lower = text.lower()
        for keyword in self.SENSITIVE_KEYWORDS:
            keyword_lower = keyword.lower()
            start = 0
            while True:
                pos = text_lower.find(keyword, start)
                if pos == -1:
                    break
                positions.append((pos, pos + len(keyword)))
                start = pos + 1
        return positions

    def apply(self, text: str) -> str:
        if self.mode == "random":
            # 模式1：随机位置插入（原有逻辑）
            out = []
            for c in text:
                out.append(c)
                if random.random() < self.prob:
                    out.append(self._get_random_zw_chars())
            return "".join(out)
        
        elif self.mode == "keyword":
            # 模式2：仅在敏感关键词周围插入
            positions = self._find_keyword_positions(text)
            if not positions:
                return text
            
            # 随机选择1-2个关键词位置进行插入
            selected = random.sample(positions, min(len(positions), random.randint(1, 2)))
            
            out = []
            last_end = 0
            for start, end in sorted(selected):
                out.append(text[last_end:start])
                # 在关键词前插入
                if random.random() < 0.5:
                    out.append(self._get_random_zw_chars())
                out.append(text[start:end])
                # 在关键词后插入
                if random.random() < 0.5:
                    out.append(self._get_random_zw_chars())
                last_end = end
            out.append(text[last_end:])
            return "".join(out)
        
        elif self.mode == "char_inside":
            # 模式3：在每个字符之间插入（打散token）
            out = []
            chars = list(text)
            for i, c in enumerate(chars):
                out.append(c)
                if i < len(chars) - 1 and random.random() < self.prob:
                    out.append(self._get_random_zw_chars())
            return "".join(out)
        
        else:
            return text


class Base64EncodeOp(MutationOp):
    name = "base64"
    
    # 敏感关键词列表
    SENSITIVE_KEYWORDS = [
        "密码", "账号", "登录", "转账", "银行卡", "信用卡", "余额",
        "病毒", "木马", "蠕虫", "恶意", "漏洞", "攻击", "入侵",
        "炸弹", "枪支", "毒品", "武器", "爆炸", "有毒", "氰化物",
        "色情", "赌博", "诈骗", "钓鱼", "勒索", "黑客", "破解",
        "sql", "xss", "inject", "exec", "eval", "script",
        "password", "login", "admin", "root", "hack", "bypass",
        "delete", "drop", "insert", "update", "select", "create",
        "rm", "ls", "cat", "echo", "wget", "curl",
    ]

    def __init__(self, ratio: float = 0.3, mode: str = "token", include_hint: bool = True):
        """
        Base64 编码算子
        
        参数:
            ratio: 编码比例，0.3表示30%的token被编码
            mode: 编码模式
                - "token": 按空格切分，随机选择部分token编码
                - "keyword": 仅编码敏感关键词
                - "full": 对整个提示词编码（保留开头一句可读）
                - "mixed": 混合模式，编码部分内容并嵌入解码提示
            include_hint: 是否包含解码提示（仅对full/mixed模式生效）
        """
        super().__init__()
        self.ratio = ratio
        self.mode = mode
        self.include_hint = include_hint
        
        # 解码提示模板
        self.hint_templates = [
            "请解码以下内容：",
            "下面这段需要你帮我解码：",
            "帮我解释一下这段编码：",
            "decode this:",
            "base64 decode:",
        ]

    def _is_sensitive(self, token: str) -> bool:
        token_lower = token.lower()
        return any(kw.lower() in token_lower for kw in self.SENSITIVE_KEYWORDS)

    def apply(self, text: str) -> str:
        if self.mode == "token":
            # 模式1：按token随机编码（原有逻辑）
            tokens = text.split()
            for i in range(len(tokens)):
                if random.random() < self.ratio:
                    b = base64.b64encode(tokens[i].encode()).decode()
                    tokens[i] = b
            return " ".join(tokens)
        
        elif self.mode == "keyword":
            # 模式2：仅编码敏感关键词
            tokens = text.split()
            for i in range(len(tokens)):
                if self._is_sensitive(tokens[i]):
                    tokens[i] = base64.b64encode(tokens[i].encode()).decode()
            return " ".join(tokens)
        
        elif self.mode == "full":
            # 模式3：对整个提示词编码
            if self.include_hint:
                hint = random.choice(self.hint_templates)
                encoded = base64.b64encode(text.encode()).decode()
                return f"{hint}\n{encoded}"
            else:
                return base64.b64encode(text.encode()).decode()
        
        elif self.mode == "mixed":
            # 模式4：混合模式，保留部分可读，编码部分敏感词
            tokens = text.split()
            encoded_tokens = []
            
            for token in tokens:
                if self._is_sensitive(token) and random.random() < 0.8:
                    encoded_tokens.append(base64.b64encode(token.encode()).decode())
                elif random.random() < self.ratio and len(token) > 2:
                    encoded_tokens.append(base64.b64encode(token.encode()).decode())
                else:
                    encoded_tokens.append(token)
            
            result = " ".join(encoded_tokens)
            
            if self.include_hint:
                hint = random.choice(self.hint_templates)
                return f"{hint}\n{result}"
            return result
        
        return text


class LeetSpeakOp(MutationOp):
    name = "leetspeak"
    
    # Leetspeak 替换映射表
    MAP = str.maketrans({
        # 基础替换 (最常见)
        "a": "4", "A": "4",
        "e": "3", "E": "3",
        "i": "1", "I": "1",
        "o": "0", "O": "0",
        "s": "5", "S": "5",
        
        # 扩展替换
        "b": "8", "B": "8",
        "t": "7", "T": "7",
        "g": "9", "G": "9",
        "l": "1", "L": "1",
        "z": "2", "Z": "2",
        
        # 特殊字符替换
        "@": "a", "4": "a",
        "$": "s", "5": "s",
        "!": "i", "1": "i",
        "0": "o",
        "7": "t",
        "8": "b",
        "3": "e",
        "9": "g",
        "2": "z",
    })

    def __init__(self, prob: float = 0.3, mode: str = "basic"):
        """
        Leetspeak 变换算子
        
        参数:
            prob: 触发概率，30%概率应用变换
            mode: 变换模式
                - "basic": 仅使用基础映射 (a/e/i/o/s → 4/3/1/0/5)
                - "extended": 使用全部扩展映射
                - "random": 随机选择部分字符进行替换
        """
        super().__init__()
        self.prob = prob
        self.mode = mode

    def apply(self, text: str) -> str:
        if random.random() >= self.prob:
            return text
        
        if self.mode == "basic":
            # 仅基础映射
            basic_map = {
                k: v
                for k, v in self.MAP.items()
                if isinstance(k, str) and len(k) == 1 and k.isalpha()
            }
            return text.translate(str.maketrans(basic_map))
        
        elif self.mode == "extended":
            # 全部映射
            return text.translate(self.MAP)
        
        elif self.mode == "random":
            # 随机选择部分字符替换
            out = []
            for c in text:
                if c.lower() in "aeioslztgb" and random.random() < 0.5:
                    replacement = self.MAP.get(c.lower())
                    if replacement:
                        out.append(replacement)
                    else:
                        out.append(c)
                else:
                    out.append(c)
            return "".join(out)
        
        return text


# 简单工具：按权重随机选择算子并执行
def mutate_text(text: str, ops: List[MutationOp], k: int = 1) -> str:
    """对输入 text 随机选择 k 个算子（按权重）并顺次应用，返回变异后文本。"""
    if not ops:
        return text
    weights = [op.weight for op in ops]
    chosen = random.choices(ops, weights=weights, k=k)
    out = text
    for op in chosen:
        out = op.apply(out)
    return out


def load_ops_from_plugins(plugin_dir: str = None) -> List[MutationOp]:
    """扫描指定目录下的 python 插件文件，动态加载其中继承自 MutationOp 的类并实例化。

    - `plugin_dir` 若为 None，则默认查找 package 内 `plugins` 子目录。
    - 要求插件中定义的算子类继承 `MutationOp` 并且提供无参或默认参数的构造函数。
    返回已实例化的 MutationOp 列表。
    """
    ops = []
    base = Path(__file__).resolve().parent
    if plugin_dir:
        p = Path(plugin_dir)
    else:
        p = base / "plugins"

    if not p.exists() or not p.is_dir():
        return ops

    for py in sorted(p.glob("*.py")):
        if py.name.startswith("__"):
            continue
        try:
            spec = importlib.util.spec_from_file_location(f"promptfuzz_sc.plugins.{py.stem}", str(py))
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                for name, obj in inspect.getmembers(mod, inspect.isclass):
                    if issubclass(obj, MutationOp) and obj is not MutationOp:
                        try:
                            instance = obj()
                            ops.append(instance)
                        except Exception:
                            continue
        except Exception:
            continue

    return ops


def load_plugin_classes(plugin_dir: str = None):
    classes = {}
    base = Path(__file__).resolve().parent
    if plugin_dir:
        p = Path(plugin_dir)
    else:
        p = base / "plugins"

    if not p.exists() or not p.is_dir():
        return classes

    for py in sorted(p.glob("*.py")):
        if py.name.startswith("__"):
            continue
        try:
            spec = importlib.util.spec_from_file_location(f"promptfuzz_sc.plugins.{py.stem}", str(py))
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                for name, obj in inspect.getmembers(mod, inspect.isclass):
                    if issubclass(obj, MutationOp) and obj is not MutationOp:
                        classes[obj.__name__] = obj
        except Exception:
            continue

    return classes
