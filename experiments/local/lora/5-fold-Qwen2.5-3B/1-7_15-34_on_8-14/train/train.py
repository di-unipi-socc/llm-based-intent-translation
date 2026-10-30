import os
import torch
from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Program to train Qwen 2.5 Coder with the native chat template

    # --- PHASE 1: LOADING THE MODEL ---
    max_seq_length = 2048

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = "unsloth/Qwen2.5-Coder-3B-Instruct",
        max_seq_length = max_seq_length,
        load_in_4bit = False,
    )

    # Apply the native chat template of Qwen 2.5
    # This configures the tokenizer to use the <|im_start|> and <|im_end|> tokens
    tokenizer = get_chat_template(
        tokenizer,
        chat_template = "qwen-2.5",
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r = 16,
        target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha = 32,
        use_gradient_checkpointing = "unsloth",
    )

    # --- PHASE 2: DATA PREPARATION ---
    # System instruction extracted directly from the dataset

    def format_examples(examples):
        """Format each example in the native conversational format of Qwen 2.5.
    
        Converts the instruction/input/output fields of the dataset into the format:
        [{"role": "system", ...}, {"role": "user", ...}, {"role": "assistant", ...}]
        and then applies the tokenizer's chat template.
        """
        instructions = examples["instruction"]
        inputs       = examples["input"]
        outputs      = examples["output"]
        texts = []
        for inst, inp, out in zip(instructions, inputs, outputs):
            # Combine instruction and input in the user message
            user_message = inp  # The input contains the natural language request
        
            # Build the conversation in the chat format
            conversation = [
                {"role": "system", "content": inst},
                {"role": "user",   "content": user_message},
                {"role": "assistant", "content": out},
            ]
        
            # Apply the native template of Qwen 2.5
            text = tokenizer.apply_chat_template(
                conversation,
                tokenize = False,
                add_generation_prompt = False,
            )
            texts.append(text)
        return { "text" : texts }

    # MODIFY HERE: insert the path of your training dataset
    dataset = load_dataset("json", data_files=os.path.normpath(os.path.join(script_dir, 'dataset_train_context1-7_15-34.jsonl')), split="train")
    dataset = dataset.map(format_examples, batched = True)

    # --- PHASE 3: TRAINING ENGINE ---
    trainer = SFTTrainer(
        model = model,
        tokenizer = tokenizer,
        train_dataset = dataset,
        dataset_text_field = "text",
        max_seq_length = max_seq_length,
        args = TrainingArguments(
            per_device_train_batch_size = 2,      
            gradient_accumulation_steps = 2,      
            num_train_epochs = 5,                
            learning_rate = 2e-4,
            weight_decay = 0.01,                                      
            fp16 = not torch.cuda.is_bf16_supported(),
            bf16 = torch.cuda.is_bf16_supported(), 
            logging_steps = 10,                   
            optim = "adamw_8bit",
            output_dir = os.path.normpath(os.path.join(script_dir, 'training_results')),
            save_strategy = "no",
        ),
    )

    trainer.train()

    # --- PHASE 4: SAVING ---
    # MODIFY HERE: name of the folder where to save the trained model
    model.save_pretrained(os.path.normpath(os.path.join(script_dir, '../tester/qwen2.5-3B-1-7_15-34')))


if __name__ == "__main__":
    main()
