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
        prompt_template = (
            "You are estimating sentiment on stock price impact. "
            "Return a number between -1 (bearish) and 1 (bullish).\nSentence: {sent}\nScore:"
        )
        scores = []
        for sent in sentences:
            prompt = prompt_template.format(sent=sent)
            out = self.generator(prompt, num_return_sequences=1)[0]["generated_text"]
            try:
                score = float(out.split("Score:")[-1].strip().split()[0])
            except Exception:
                score = 0.0
            scores.append(max(min(score, 1.0), -1.0))
        return scores
