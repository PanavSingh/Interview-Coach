import json
import os
import logging

logger = logging.getLogger(__name__)

FALLBACK_QUESTIONS = {
    "Technology": [
        "Describe a complex technical problem you solved recently. What was your approach?",
        "How do you stay current with emerging technologies in your field?",
        "Tell me about a time you had to make a trade-off between speed and quality.",
        "How do you approach debugging a production issue under pressure?",
        "Describe your experience working in agile or cross-functional teams.",
    ],
    "Human Resources": [
        "How do you handle conflict resolution between team members?",
        "Describe your approach to building an inclusive workplace culture.",
        "Tell me about a difficult hiring decision you had to make.",
        "How do you measure employee engagement and act on the results?",
        "Describe a time you had to deliver difficult feedback to an employee.",
    ],
    "default": [
        "Tell me about yourself and what drives you professionally.",
        "What are your greatest strengths, and how have they helped you succeed?",
        "Describe a significant challenge you faced and how you overcame it.",
        "Why do you want this role, and what makes you the ideal candidate?",
        "Where do you see yourself in 5 years, and how does this role fit that vision?",
    ],
}


def _get_ai_client():
    # Priority: Groq (free) > OpenAI > Gemini
    api_key = os.environ.get("GROQ_API_KEY")
    if api_key:
        try:
            from groq import Groq
            return "groq", Groq(api_key=api_key)
        except ImportError:
            logger.warning("groq package not installed")

    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        try:
            import openai
            return "openai", openai.OpenAI(api_key=api_key)
        except ImportError:
            logger.warning("openai package not installed")

    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        try:
            from google import genai
            return "gemini", genai.Client(api_key=api_key)
        except ImportError:
            logger.warning("google-genai package not installed")

    return None, None


def _call_ai(prompt):
    client_type, client = _get_ai_client()
    if client_type == "groq":
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1024,
        )
        return resp.choices[0].message.content.strip()
    elif client_type == "openai":
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1024,
        )
        return resp.choices[0].message.content.strip()
    elif client_type == "gemini":
        resp = client.models.generate_content(
            model="gemini-2.0-flash", contents=prompt,
        )
        return resp.text.strip()
    return None


def generate_questions(domain, role, skills="", experience="", count=5):
    prompt = (
        f"Generate exactly {count} interview questions for a {role} position "
        f"in the {domain} domain.\n"
    )
    if skills:
        prompt += f"Key skills: {skills}\n"
    if experience:
        prompt += f"Experience: {experience}\n"
    prompt += (
        "Return ONLY a JSON array of strings, no extra text. "
        "Example: [\"Question 1?\", \"Question 2?\"]"
    )

    try:
        result = _call_ai(prompt)
        if result:
            text = result.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                text = text.rsplit("```", 1)[0]
            questions = json.loads(text.strip())
            if isinstance(questions, list) and len(questions) >= count:
                return questions[:count]
    except Exception as e:
        logger.error(f"AI question generation failed: {e}")

    return FALLBACK_QUESTIONS.get(domain, FALLBACK_QUESTIONS["default"])[:count]


def evaluate_answer(question, answer, domain, role):
    if not answer or not answer.strip():
        return {"score": 0, "feedback": "No answer provided."}

    prompt = (
        f"You are an expert interviewer for {role} in {domain}.\n"
        f"Question: {question}\n"
        f"Candidate's answer: {answer}\n\n"
        "Evaluate the answer. Return ONLY valid JSON with:\n"
        '- "score": integer 1-10\n'
        '- "feedback": string with 2-3 sentences of constructive feedback\n'
        'Example: {"score": 7, "feedback": "Good structure but could add more specifics."}'
    )

    try:
        result = _call_ai(prompt)
        if result:
            text = result.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                text = text.rsplit("```", 1)[0]
            data = json.loads(text.strip())
            return {
                "score": int(data.get("score", 5)),
                "feedback": data.get("feedback", ""),
            }
    except Exception as e:
        logger.error(f"AI evaluation failed: {e}")

    return {"score": 5, "feedback": "AI evaluation was temporarily unavailable. A default score of 5/10 has been assigned. Please try again for accurate feedback."}
