import asyncio
import random
import time
from typing import List, Optional, Tuple
from .mutation import MutationOp, mutate_text
from .client import DeepSeekClient
from .metrics import stealth_score, compute_msr, compute_aqs


class EpsGreedySearcher:
    def __init__(self, client: DeepSeekClient, ops: List[MutationOp], concurrency: int = 8):
        self.client = client
        self.ops = ops
        self.concurrency = concurrency

    async def _score_prompt(self, prompt: str) -> Tuple[bool, str]:
        data = await self.client.call(prompt)
        if isinstance(data, dict) and "success" in data:
            return bool(data["success"]), data.get("resp", "")
        return False, str(data)

    async def search(
        self,
        seed_prompts: List[str],
        budget: int = 10000,
        eps: float = 0.2,
        max_iters: Optional[int] = None,
        metrics=None,
    ) -> dict:

        sem = asyncio.Semaphore(self.concurrency)
        queries = 0
        best = [] 
        history = []

        success_count = 0
        queries_to_success = []  
        stealth_values = []      

        async def worker(prompt: str):
            nonlocal queries
            async with sem:
                queries += 1
                return await self._score_prompt(prompt)

        population = list(seed_prompts)
        scores = {p: 0 for p in population}
        trials = {p: 0 for p in population}

        start = time.time()
        iters = 0
        while queries < budget and (max_iters is None or iters < max_iters):
            iters += 1
            if random.random() < eps or not best:
                parent = random.choice(population)
            else:
                parent = random.choice([b[0] for b in best[:max(1, len(best))]])

            k = random.choice([1, 2])
            child = mutate_text(parent, self.ops, k=k)

            succ, resp = await worker(child)

            trials[parent] = trials.get(parent, 0) + 1
            history.append({"prompt": child, "success": succ, "resp": resp, "iter": iters})

            # 维护 best 列表（简单按最近成功率）
            if succ:
                stealth = stealth_score(parent, child)
                best.insert(0, (child, 1.0, queries, resp, stealth))
                success_count += 1
                queries_to_success.append(queries)
                stealth_values.append(stealth)
                seen = set()
                newbest = []
                for item in best:
                    if item[0] not in seen:
                        seen.add(item[0])
                        newbest.append(item)
                best = newbest[:50]

            # 局部精修
            if best and random.random() < 0.3:
                candidate = best[0][0]
                refined = await self._hill_climb(candidate, worker, steps=5)
                if refined:
                    best.insert(0, refined)
                    seen = set(); nb = []
                    for item in best:
                        if item[0] not in seen:
                            seen.add(item[0]); nb.append(item)
                    best = nb[:50]

            # 更新 Prometheus 等外部度量
            if metrics is not None and queries > 0:
                msr = compute_msr(success_count, queries)
                aqs = compute_aqs(queries_to_success) if queries_to_success else float("nan")
                stealth_mean = float(sum(stealth_values) / len(stealth_values)) if stealth_values else float("nan")
                try:
                    metrics.update(
                        msr=msr,
                        aqs=aqs,
                        stealth_mean=stealth_mean,
                        total_queries=queries,
                        success_count=success_count,
                    )
                except Exception:
                    pass

        end = time.time()
        return {"best": best, "history": history, "queries": queries, "elapsed": end - start}

    async def _hill_climb(self, prompt: str, worker, steps: int = 5):
        """对 prompt 进行局部微调，返回最优成功项或 None。"""
        current = prompt
        for _ in range(steps):
            child = mutate_text(current, self.ops, k=1)
            succ, resp = await worker(child)
            if succ:
                stealth = stealth_score(prompt, child)
                return (child, 1.0, None, resp, stealth)
            if random.random() < 0.2:
                current = child
        return None
