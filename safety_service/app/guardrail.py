from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from app.config import GUARDRAIL_MODEL_NAME

def format_prompt(text: str) -> str:
    return f"[INPUT]: {text} [OUTPUT]:"

class LlamaGuardModel:
    """
    LLaMA Guard를 생성 모델로 활용하여 생성 결과 텍스트를 통해
    입력 텍스트의 안전성을 판단하는 클래스.
    """
    def __init__(self, model_name=GUARDRAIL_MODEL_NAME):
        print(f"[LlamaGuardModel] Loading model {model_name}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        # GPU 사용 시: self.model.to("cuda")

    def predict_batch(self, texts: list[str]) -> list[str]:
        """
        배치 입력에 대해 생성 모델로부터 응답을 받고,
        생성 결과 텍스트에 "\n\nunsafe" (옵션: \nS1 ~ \nS15)가 있으면 unsafe, 
        "\n\nsafe"가 있으면 safe로 판단합니다.
        """
        prompts = [format_prompt(t) for t in texts]
        inputs = self.tokenizer(prompts, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            outputs = self.model.generate(**inputs, max_new_tokens=20)
        generated_texts = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
        results = []
        for gen in generated_texts:
            if "unsafe" in gen.lower():
                results.append("unsafe")
            else:
                results.append("safe")
        return results
