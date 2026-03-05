# chatbot_with_memory_continue.py

import json
import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from trustguard import TrustGuard
from trustguard.schemas import GenericResponse
from trustguard.rules import validate_pii  # PII detection only

from memory import ChatMemory  # your memory.py

# =====================================
# 1️⃣ Load Environment Variables
# =====================================

load_dotenv()
HF_TOKEN = os.getenv("HF_API_KEY")
if not HF_TOKEN:
    raise ValueError("HF_API_KEY not found in environment variables.")

# =====================================
# 2️⃣ Initialize HuggingFace LLM
# =====================================

llm = InferenceClient(
    model="openai/gpt-oss-20b",
    token=HF_TOKEN
)

# =====================================
# 3️⃣ TrustGuard with PII Detection
# =====================================

input_guard = TrustGuard(schema_class=GenericResponse, custom_rules=[validate_pii])
output_guard = TrustGuard(schema_class=GenericResponse, custom_rules=[validate_pii])

# =====================================
# 4️⃣ Initialize Chat Memory
# =====================================

chat_memory = ChatMemory()  # optional: ChatMemory(max_len=20) to limit size

# Keywords for continuation
CONTINUE_KEYWORDS = ["cont", "continue", "more", "keep going", "again", "yes", "y"]

# Track if bot asked "Do you want more details?"
pending_continuation = False

# =====================================
# 5️⃣ Chat Function with “Ask Before Continuing”
# =====================================

def chat(user_message: str):
    global pending_continuation
    user_message = user_message.strip()
    user_message_lower = user_message.lower()

    if not user_message:
        return "⚠️ Please enter a message."

    # ---- Handle continuation request ----
    if pending_continuation and user_message_lower in CONTINUE_KEYWORDS:
        user_message = "Please continue from last answer."
    pending_continuation = False  # reset after user responds

    # ---- INPUT VALIDATION ----
    input_payload = json.dumps({
        "content": user_message,
        "sentiment": "neutral",
        "tone": "neutral",
        "is_helpful": True
    })
    input_result = input_guard.validate(input_payload)
    if not input_result.is_approved:
        return f"🚫 Blocked (Input - PII): {input_result.log}"

    # ---- Add user message to memory ----
    chat_memory.add_user_message(user_message)

    # ---- Build messages for LLM ----
    system_prompt = (
        "You are a helpful AI assistant. "
        "Answer the user concisely and naturally. "
        "Do NOT output any internal reasoning or <think> tags. "
        "If your answer can be expanded or has additional details, "
        "end your response with 'Do you want more details?'."
    )

    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_memory.get_full_history():
        messages.append({"role": msg["role"], "content": msg["content"]})

    # ---- LLM Generation ----
    try:
        response = llm.chat_completion(
            messages=messages,
            max_tokens=2048,
            temperature=0.7,
        )
        reply = response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Model Error: {str(e)}"

    if not reply:
        return "⚠️ Model returned empty output."

    # ---- Add assistant reply to memory ----
    chat_memory.add_assistant_message(reply)

    # ---- Check if bot asked for more details ----
    if "do you want more details" in reply.lower():
        pending_continuation = True

    # ---- OUTPUT VALIDATION ----
    output_payload = json.dumps({
        "content": reply,
        "sentiment": "neutral",
        "tone": "neutral",
        "is_helpful": True
    })
    output_result = output_guard.validate(output_payload)
    if not output_result.is_approved:
        return f"⚠️ Blocked (Output - PII): {output_result.log}"

    # ---- Clean reply ----
    clean_reply = output_result.data['content'].replace("<think>", "").replace("</think>", "").strip()
    return clean_reply

# =====================================
# 6️⃣ CLI Chat Loop
# =====================================

if __name__ == "__main__":
    print("🤖 Chatbot with Memory + 'Ask Before Continuing' + PII Detection")
    print("(type 'exit' to quit)\n")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break
        print("Bot:", chat(user_input))