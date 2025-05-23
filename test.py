from huggingface_hub import InferenceClient

client = InferenceClient(
    model="deepseek-ai/DeepSeek-V3",
    token="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",
    provider="novita"
)

try:
    response = client.chat_completion(
        messages=[{"role": "user", "content": "Test prompt: list some files"}],
        max_tokens=50
    )
    print("Response:", response.choices[0].message.content)
except Exception as e:
    print("Error:", str(e))