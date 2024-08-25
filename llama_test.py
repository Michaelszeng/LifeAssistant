from huggingface_hub import login, snapshot_download
from data_files.data import huggingface_token
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
    
    system_prompt="""
        You are a highly selective automated reminder system. Your task is to evaluate the relevance of an event or task against a list of 
        reminder items. Only generate a reminder if there is a clear and direct connection between the event or task and the reminder items. 
        Respond with 'True/False: "Reminder text"', where 'True' indicates a valid reminder, and 'False' indicates no relevance. Ensure 
        reminders are concise (up to 12 words) and optimistic/exciting. If uncertain, default to 'False' with an empty reminder text.
    """

    system_prompt = system_prompt.replace('\n', '')

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
        do_sample=False,  # Deterministic output
    )

    text = outputs[0]["generated_text"][len(prompt):]
    wrapped_text = wrap_text(text)
    print(input_text)
    print()
    print(wrapped_text)
    print("\n-----------------------------------------------------------------------------------------------------------------\n")

    return wrapped_text


from data_files.reminders import *
ordered_reminders = "\n".join(f"{i+1}. {reminder}" for i, reminder in enumerate(reminders))

llm_inference(f"""Here is the task or event name: {"6.1210 Final"}.\n\nHere is a list of things I would like you to remind me about: \n{ordered_reminders}\n\nOtherwise, do not write a reminder at all.""", max_length=100)

llm_inference(f"""Here is the task or event name: {"Tennis with Sam"}.\n\nHere is a list of things I would like you to remind me about: \n{ordered_reminders}\n\nOtherwise, do not write a reminder at all.""", max_length=100)

llm_inference(f"""Here is the task or event name: {"UROP Payroll"}.\n\nHere is a list of things I would like you to remind me about: \n{ordered_reminders}\n\nOtherwise, do not write a reminder at all.""", max_length=100)

llm_inference(f"""Here is the task or event name: {"Robotics @ MIT Seminar"}.\n\nHere is a list of things I would like you to remind me about: \n{ordered_reminders}\n\nOtherwise, do not write a reminder at all.""", max_length=100)

llm_inference(f"""Here is the task or event name: {"Deal with house expenses"}.\n\nHere is a list of things I would like you to remind me about: \n{ordered_reminders}\n\nOtherwise, do not write a reminder at all.""", max_length=100)

llm_inference(f"""Here is the task or event name: {"free time: supercloud tutorial"}.\n\nHere is a list of things I would like you to remind me about: \n{ordered_reminders}\n\nOtherwise, do not write a reminder at all.""", max_length=100)

llm_inference(f"""Here is the task or event name: {"Book flight to SD"}.\n\nHere is a list of things I would like you to remind me about: \n{ordered_reminders}\n\nOtherwise, do not write a reminder at all.""", max_length=100)

llm_inference(f"""Here is the task or event name: {"Flight to SAN"}.\n\nHere is a list of things I would like you to remind me about: \n{ordered_reminders}\n\nOtherwise, do not write a reminder at all.""", max_length=100)

llm_inference(f"""Here is the task or event name: {"Flight to BOS"}.\n\nHere is a list of things I would like you to remind me about: \n{ordered_reminders}\n\nOtherwise, do not write a reminder at all.""", max_length=100)

llm_inference(f"""Here is the task or event name: {"Get Blood Test"}.\n\nHere is a list of things I would like you to remind me about: \n{ordered_reminders}\n\nOtherwise, do not write a reminder at all.""", max_length=100)