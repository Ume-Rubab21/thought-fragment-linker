import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq

app = FastAPI(title="Thought Fragment Linker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


# TEMPORARY — only for Day 1 Step 10 verification.
# Delete this endpoint once you've confirmed the key works;
# it should not exist in your final product.
@app.get("/test-groq")
def test_groq():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return {"error": "GROQ_API_KEY not found in environment"}

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": "Say 'Groq key works!' and nothing else."}
            ],
        )
        return {
            "success": True,
            "model_reply": response.choices[0].message.content,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}