from huggingface_hub import login
from data import huggingface_token
login(token=huggingface_token)

import os
import torch
import transformers
from transformers import AutoTokenizer, AutoModelForCausalLM
import textwrap

torch.set_default_device('cuda')

tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B-Instruct")

pipe = transformers.pipeline(
    "text-generation",
    model="meta-llama/Meta-Llama-3-8B-Instruct",
    model_kwargs={
        "torch_dtype": torch.bfloat16,
        "quantization_config": {"load_in_4bit": True},
        "low_cpu_mem_usage": True,
    },
    device="cuda",
)

def wrap_text(text, width=90): #preserve_newlines
    # Split the input text into lines based on newline characters
    lines = text.split('\n')

    # Wrap each line individually
    wrapped_lines = [textwrap.fill(line, width=width) for line in lines]

    # Join the wrapped lines back together using newline characters
    wrapped_text = '\n'.join(wrapped_lines)

    return wrapped_text


def generate(input_text, system_prompt="",max_length=512):
    if system_prompt != "":
        system_prompt = system_prompt
    else:
        system_prompt = "You are a friendly and helpful assistant"
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {"role": "user", "content": input_text},
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

    outputs = pipe(
        prompt,
        max_new_tokens=max_length,
        eos_token_id=terminators,
        do_sample=False,
        temperature=0.0,
        top_p=0.9,
    )

    text = outputs[0]["generated_text"][len(prompt):]
    wrapped_text = wrap_text(text)
    print(wrapped_text)


generate('Write a detailed analogy between mathematics and a lighthouse.',
         system_prompt="You are a helpful assistant called Llama-3. Write out your reasoning step-by-step to be sure you get the right answers!",
         max_length=1024)