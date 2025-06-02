def build_prompt(context: str, question: str, start_time: str = None, end_time: str = None) -> str:
    intro = (
        "You are a friendly, supportive tutor helping a student understand a lesson from a video and its materials.\n"
        "Respond clearly, kindly, and helpfully.\n"
    )
    time_note = ""
    if start_time and end_time:
        time_note = f"\nThe student is asking about content between **{start_time}** and **{end_time}**.\n"
    elif start_time:
        time_note = f"\nThe student is asking about content near **{start_time}**.\n"

    return f"""{intro}{time_note}

Context:
---
{context}
---

Student's question:
"{question}"

Answer as a helpful tutor:"""
