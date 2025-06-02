from openai import OpenAI
import re

client = OpenAI(api_key="188d6df2c6c200770a9497c14c5b9ad37abe4ee69d0f97f16b6d73ef7c89b7f3", base_url="https://api.together.xyz/v1")  # or openai.OpenAI(...) if needed

def clean_response(text):
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

def generate_local_answer(prompt, tag=""):
    response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
        messages=[
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=512,
    )
    return clean_response(response.choices[0].message.content.strip())
