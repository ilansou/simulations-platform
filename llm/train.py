from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from trl import SFTTrainer
from datasets import load_dataset
import torch
from peft import LoraConfig
import os
from dotenv import load_dotenv

load_dotenv()

def train_model():
    try:
        # Load base model
        model_name = "deepseek-ai/deepseek-coder-1.3b-base"
        model = AutoModelForCausalLM.from_pretrained(model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name)

        # Prepare dataset
        dataset = load_dataset("your_dataset_or_path")

        # Configure LoRA
        peft_config = LoraConfig(
            r=16,
            lora_alpha=32,
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM"
        )

        # Configure the trainer
        trainer = SFTTrainer(
            model=model,
            train_dataset=dataset,
            peft_config=peft_config,
            dataset_text_field="text",
            max_seq_length=512,
            tokenizer=tokenizer,
            args=TrainingArguments(
                per_device_train_batch_size=4,
                gradient_accumulation_steps=4,
                warmup_steps=100,
                max_steps=1000,
                learning_rate=2e-4,
                fp16=True,
                logging_steps=10,
                output_dir="outputs",
                save_strategy="steps",
                save_steps=100,
            )
        )

        # Start training
        trainer.train()

        # Save the model
        trainer.model.save_pretrained("./outputs/final_model")
        tokenizer.save_pretrained("./outputs/final_model")

    except Exception as e:
        print(f"An error occurred during training: {e}")

if __name__ == "__main__":
    train_model()
