from huggingface_hub import login, snapshot_download
from data import huggingface_token
login(token=huggingface_token)

import os
import torch
import transformers
from transformers import AutoTokenizer, AutoModelForCausalLM
import textwrap

torch.set_default_device('cuda')

# Download the model snapshot to a specific directory
MODEL_DIR = 'llama'
model_dir = snapshot_download(
    repo_id="meta-llama/Meta-Llama-3-8B-Instruct",
    revision="main",
    local_dir=MODEL_DIR
)


tokenizer = AutoTokenizer.from_pretrained(model_dir)

pipe = transformers.pipeline(
    "text-generation",
    model=model_dir,
    model_kwargs={
        "torch_dtype": torch.bfloat16,
        "quantization_config": {"load_in_4bit": True},
        "low_cpu_mem_usage": True,
    },
    # device="cuda",
)


def llm_inference(input_text ,max_length=512):
    """
    Perform a Llama inference based on the task/calendar event data.
    """
    def wrap_text(text, width=90):
        lines = text.split('\n')
        wrapped_lines = [textwrap.fill(line, width=width) for line in lines]  # Wrap each line individually
        wrapped_text = '\n'.join(wrapped_lines)  # Join the wrapped lines back together using newline characters
        return wrapped_text
    
    system_prompt="You are a helpful assistant called Llama-3. Write out your reasoning step-by-step to be sure you get the right answers!"
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {   
            "role": "user", 
            "content": input_text,
        },
    ]

    prompt = pipe.tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    terminators = [
        pipe.tokenizer.eos_token_id,
        pipe.tokenizer.convert_tokens_to_ids("<|eot_id|>")
    ]

    print("BEGINNING INFERENCE")
    outputs = pipe(
        prompt,
        max_new_tokens=max_length,
        eos_token_id=terminators,
        do_sample=True,  # Probabilistically sample output
        temperature=0.0,
        top_p=0.9,
    )

    text = outputs[0]["generated_text"][len(prompt):]
    wrapped_text = wrap_text(text)
    print(wrapped_text)

    return wrapped_text


llm_inference('What is 1+1?', max_length=100)