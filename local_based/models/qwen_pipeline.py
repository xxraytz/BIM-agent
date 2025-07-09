from __future__ import annotations
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

MODEL_ID = "Qwen/Qwen3-8B"


def load_qwen_pipeline(*, device_map="auto"):
    """Return HF pipeline ready for generation."""
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, torch_dtype="auto", 
        device_map="auto",
        # max_memory={0: "4GiB", 1: "0GiB", 2: "32GiB", 3: "32GiB"},
        trust_remote_code=True,
    )
    return pipeline("text-generation", model=model, tokenizer=tokenizer)