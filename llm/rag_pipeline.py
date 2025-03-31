from transformers import AutoTokenizer, AutoModelForCausalLM

class RAGPipeline:
    def __init__(self):
        model_name = "deepseek-ai/deepseek-coder-1.3b-base"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)

    def query(self, question: str) -> str:
        inputs = self.tokenizer.encode(question, return_tensors="pt")
        outputs = self.model.generate(
            inputs,
            max_length=128,
            num_return_sequences=1,
            pad_token_id=self.tokenizer.eos_token_id
        )
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
