from groq import Groq
from src.config import GROQ_API_KEY, MODEL
client = Groq(api_key=GROQ_API_KEY)


SYSTEM_PROMPT = """
You are a senior software engineer doing a code review.
Analyze the given code and return structured feedback in this exact format:

BUGS: <list any bugs or logical errors, or 'None found'>
SECURITY: <list any security issues, or 'None found'>
STYLE: <list any code style or readability issues, or 'None found'>
SUGGESTIONS: <list any improvements, or 'None'>
SEVERITY: <overall severity: LOW / MEDIUM / HIGH>

FIXED_CODE:
```<language>
<the complete fixed code for this file>
```

Be concise for the review part. Max 5 points per section. If no bugs or improvements are needed, you must still provide the FIXED_CODE section exactly as the original code.
"""

def review_file(filename: str, content: str) -> dict:
    try:
        print(f"[reviewer] reviewing {filename}...")

        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=4000,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"File: {filename}\n\n```\n{content}\n```"}
            ]
        )

        full_response = response.choices[0].message.content
        
        # Parse out the fixed code
        review_part = full_response
        fixed_code = ""
        
        if "FIXED_CODE:" in full_response:
            parts = full_response.split("FIXED_CODE:")
            review_part = parts[0].strip()
            fixed_code_part = parts[1].strip()
            
            import re
            match = re.search(r'```[a-zA-Z]*\n(.*?)```', fixed_code_part, re.DOTALL)
            if match:
                fixed_code = match.group(1).strip()
            else:
                # If no backticks found, just use the raw text and strip any leading markdown bold/stars
                fixed_code = fixed_code_part.strip().lstrip('*').strip()

        return {"review": review_part, "fixed_code": fixed_code}

    except Exception as e:
        print(f"[reviewer] failed to review {filename}: {e}")
        return {"review": f"[reviewer] failed to review {filename}: {e}", "fixed_code": ""}