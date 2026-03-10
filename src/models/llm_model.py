from __future__ import annotations

from typing import List

from loguru import logger
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

from src.utils.config import Settings


class LLMScorer:
    def __init__(self, config: Settings):
        self.config = config
        model_name = config.llm.model_name
        logger.info(f"Loading LLM model {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        self.generator = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_new_tokens=config.llm.max_tokens,
            temperature=config.llm.temperature,
            top_p=config.llm.top_p,
        )

    def score_sentences(self, sentences: List[str]) -> List[float]:
        # Offline/low-resource safe scoring: simple heuristic without generation to avoid crashes
        scores: List[float] = []
        for sent in sentences:
            lower = sent.lower()
            if any(w in lower for w in ["surge", "beat", "upgrade", "record", "rise", "bull"]):
                scores.append(0.4)
            elif any(w in lower for w in ["miss", "downgrade", "probe", "fall", "bear", "layoff"]):
                scores.append(-0.4)
            else:
                scores.append(0.0)
        return scores
