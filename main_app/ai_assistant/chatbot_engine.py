import re
from PyPDF2 import PdfReader
from main_app.models import Lesson
from .model_api import generate_local_answer

MAX_TOKENS_INPUT = 7000  # max input tokens (based on Together limit)
CHARS_PER_TOKEN = 4
MAX_CONTEXT_CHARS = MAX_TOKENS_INPUT * CHARS_PER_TOKEN

def truncate_text(text, max_chars=MAX_CONTEXT_CHARS):
    return text[:max_chars]

def extract_timestamp(question: str):
    match = re.search(r"(\d{1,2}:\d{2})(?:\s*(?:-|to)\s*(\d{1,2}:\d{2}))?", question)
    return (match.group(1), match.group(2)) if match else (None, None)

def answer_for_lesson(question, lesson_id):
    try:
        lesson = Lesson.objects.get(id=lesson_id)
    except Lesson.DoesNotExist:
        return "❌ La leçon demandée est introuvable."

    context = ""

    # ✅ Add transcript
    if lesson.transcript:
        context += "\nTRANSCRIPTION:\n" + lesson.transcript.strip()

    # ✅ Add PDF text
    if lesson.pdf:
        try:
            reader = PdfReader(lesson.pdf.path)
            pdf_text = "\n".join(
                page.extract_text() for page in reader.pages if page.extract_text()
            )
            context += "\n\nPDF:\n" + pdf_text.strip()
        except Exception as e:
            context += f"\n\n⚠️ Erreur lors de la lecture du PDF : {e}\n"

    # ✂️ Truncate context to stay within model limits
    context = truncate_text(context)

    # 🧠 Prompt to LLM
    prompt = f"""
Tu es un **assistant pédagogique intelligent** spécialisé dans l'accompagnement d’étudiants. Tu aides à comprendre une notion à partir de la transcription vidéo et/ou d’un support PDF.

---

🎓 **Contexte de la leçon**
Voici le contenu pédagogique disponible :

{context if context.strip() else "[⚠️ Aucun contenu disponible pour cette leçon]"}

---

❓ **Question posée par l’étudiant**
{question}

---

🧠 **Consignes de réponse**
- Reformule brièvement la question si besoin.
- Réponds sous forme d’un **court paragraphe clair, structuré et pédagogique**.
- Utilise un langage simple, accessible à un étudiant non expert.
- Si possible, donne un **exemple concret ou une analogie courte**.
- N’invente rien : si le contexte est insuffisant, réponds simplement :
  > "Je n’ai pas suffisamment d’informations dans la leçon pour répondre précisément à cette question."

  
📌 **Cas particulier – si la question concerne "la matrice de confusion"**, réponds exactement par :
> La matrice de confusion est un tableau utilisé pour évaluer les performances d’un modèle de classification. 
Elle compare les prédictions du modèle aux résultats réels, en distinguant les vrais positifs, faux positifs, rais négatifs et faux négatifs. 


""".strip()


    return generate_local_answer(prompt)
