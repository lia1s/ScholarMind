import re
from collections import Counter
from pathlib import Path

import fitz
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {"pdf", "txt"}

STOP_WORDS = set("""
a an the and or but if then than of in on at to for from by with
is are was were be been being it its this that these those as
can could should would will may might must do does did have has had
not no we they you he she them their our your i me my us
about into over under between through during before after also
such more most some any each every other only very when where
which who what why how all both few many much own same so too
there here because while up out use used using
""".split())

CYBER_DEFINITIONS = {
    "cybersecurity": "The practice of protecting systems, networks, and data from digital attacks.",
    "confidentiality": "Ensuring that information is accessible only to authorized people.",
    "integrity": "Maintaining the accuracy and completeness of information.",
    "availability": "Ensuring that systems and information are accessible when needed.",
    "authentication": "Verifying the identity of a user or system.",
    "authorization": "Determining what an authenticated user is allowed to access.",
    "firewall": "A security control that monitors and filters network traffic.",
    "phishing": "A deceptive attempt to obtain sensitive information by impersonation.",
    "malware": "Software designed to harm, disrupt, or gain unauthorized access to systems.",
    "encryption": "Transforming readable information into a protected encoded form.",
    "password": "A secret string used to help verify identity or protect access.",
    "network": "A group of connected devices that communicate and share resources.",
    "incident": "An event that threatens the confidentiality, integrity, or availability of information.",
    "vulnerability": "A weakness that could be exploited to affect a system.",
    "threat": "A potential cause of harm to a system, organization, or information.",
    "risk": "The possibility that a threat will exploit a weakness and cause harm.",
    "backup": "A separate copy of information used for recovery.",
    "privacy": "The appropriate handling and protection of personal information.",
    "multifactor": "Using two or more different types of evidence to verify identity.",
    "patch": "An update that fixes problems or security weaknesses in software.",
}

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def extract_text(file_storage):
    filename = secure_filename(file_storage.filename)
    extension = filename.rsplit(".", 1)[1].lower()

    if extension == "txt":
        raw = file_storage.read()
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw.decode("latin-1", errors="replace")
        return text.strip()

    if extension == "pdf":
        content = file_storage.read()
        document = fitz.open(stream=content, filetype="pdf")
        try:
            pages = [page.get_text("text") for page in document]
            return "\n".join(pages).strip()
        finally:
            document.close()

    return ""


def split_sentences(text):
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []

    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", cleaned)
    return [
        sentence.strip()
        for sentence in sentences
        if len(sentence.strip()) > 20
    ]


def get_words(text):
    return re.findall(r"\b[a-zA-Z][a-zA-Z'-]{2,}\b", text.lower())


def extract_keywords(text, limit=8):
    words = [
        word for word in get_words(text)
        if word not in STOP_WORDS
    ]

    counts = Counter(words)
    return [word for word, _ in counts.most_common(limit)]


def make_key_terms(text):
    words = extract_keywords(text, limit=10)
    terms = []

    for word in words:
        definition = CYBER_DEFINITIONS.get(
            word,
            f"An important term found in the uploaded material. Review its meaning in the source document."
        )
        terms.append({
            "term": word.capitalize(),
            "definition": definition,
        })

    return terms


def create_objectives(key_terms):
    objectives = []

    for item in key_terms[:4]:
        objectives.append(
            f"Explain the meaning and importance of {item['term'].lower()}."
        )

    if not objectives:
        objectives = [
            "Identify the main ideas presented in the learning material.",
            "Explain important concepts using information from the source.",
            "Apply the main ideas to a relevant learning question.",
        ]

    return objectives


def create_lesson_plan(text, subject, level, duration):
    sentences = split_sentences(text)
    minutes = int(duration)

    warmup = max(5, round(minutes * 0.15))
    teaching = max(10, round(minutes * 0.40))
    activity = max(5, round(minutes * 0.25))
    review = max(5, minutes - warmup - teaching - activity)

    if sentences:
        overview = sentences[0]
    else:
        overview = (
            f"Introduce the central concepts of {subject} "
            "and connect them to students' existing knowledge."
        )

    return [
        {
            "title": f"1. Introduction · {warmup} minutes",
            "items": [
                f"Introduce the topic: {subject}.",
                "Ask students what they already know about the subject.",
                f"Connect the discussion to the lesson level: {level}.",
            ],
        },
        {
            "title": f"2. Main concepts · {teaching} minutes",
            "items": [
                overview,
                "Explain the important concepts using the uploaded source.",
                "Pause for questions and clarify unfamiliar terminology.",
            ],
        },
        {
            "title": f"3. Guided practice · {activity} minutes",
            "items": [
                "Ask students to explain one key idea in their own words.",
                "Complete selected quiz questions together.",
                "Discuss why the correct answers are supported by the material.",
            ],
        },
        {
            "title": f"4. Review and assessment · {review} minutes",
            "items": [
                "Review the main learning objectives.",
                "Use the short-answer questions to check understanding.",
                "Summarize the most important points from the lesson.",
            ],
        },
    ]


def create_quiz(sentences, key_terms):
    quiz = []

    for index, sentence in enumerate(sentences[:5]):
        words = re.findall(r"\b[A-Za-z][A-Za-z'-]{3,}\b", sentence)
        candidates = [
            word for word in words
            if word.lower() not in STOP_WORDS
        ]

        if not candidates:
            continue

        answer = max(candidates, key=len)
        question_text = re.sub(
            re.escape(answer),
            "________",
            sentence,
            count=1,
            flags=re.IGNORECASE,
        )

        distractors = [
            term["term"]
            for term in key_terms
            if term["term"].lower() != answer.lower()
        ]

        options = [answer]
        for distractor in distractors:
            if distractor.lower() not in {
                option.lower() for option in options
            }:
                options.append(distractor)
            if len(options) == 4:
                break

        while len(options) < 4:
            options.append(f"None of the above ({len(options)})")

        # Deterministic rotation so the correct option is not always first.
        shift = index % len(options)
        options = options[shift:] + options[:shift]

        quiz.append({
            "question": f"Complete the statement: {question_text}",
            "options": options,
            "answer": answer,
        })

    if not quiz:
        quiz.append({
            "question": "What should students do when studying this material?",
            "options": [
                "Review the source and identify its main ideas",
                "Ignore the source",
                "Avoid asking questions",
                "Memorize unrelated information",
            ],
            "answer": "Review the source and identify its main ideas",
        })

    return quiz


def create_short_answers(sentences):
    questions = []

    for sentence in sentences[:4]:
        questions.append(
            f"Explain the main idea of this statement in your own words: {sentence}"
        )

    if not questions:
        questions = [
            "What are the main ideas presented in the document?",
            "Which concept do you consider most important, and why?",
            "How could you apply one idea from this lesson?",
        ]

    return questions


def analyze_document(text, subject, level, duration):
    sentences = split_sentences(text)
    key_terms = make_key_terms(text)

    return {
        "subject": subject,
        "level": level,
        "duration": duration,
        "lesson_plan": create_lesson_plan(
            text, subject, level, duration
        ),
        "objectives": create_objectives(key_terms),
        "key_terms": key_terms,
        "quiz": create_quiz(sentences, key_terms),
        "short_answers": create_short_answers(sentences),
        "source_preview": text[:1800],
        "word_count": len(text.split()),
        "sentence_count": len(sentences),
    }


@app.route("/", methods=["GET", "POST"])
def index():
    analysis = None
    error = None

    if request.method == "POST":
        uploaded_file = request.files.get("document")
        subject = request.form.get(
            "subject", "General lesson"
        ).strip()
        level = request.form.get("level", "Beginner")
        duration = request.form.get("duration", "45")

        if not uploaded_file or not uploaded_file.filename:
            error = "Please choose a PDF or TXT document."
        elif not allowed_file(uploaded_file.filename):
            error = "Unsupported file type. Please upload a PDF or TXT file."
        elif not subject:
            error = "Please enter a subject or topic."
        elif level not in {"Beginner", "Intermediate", "Advanced"}:
            error = "Please select a valid student level."
        elif duration not in {"30", "45", "60", "90"}:
            error = "Please select a valid lesson duration."
        else:
            try:
                source_text = extract_text(uploaded_file)

                if len(source_text.strip()) < 40:
                    error = (
                        "Not enough readable text was found. "
                        "Try a text-based PDF or a TXT file."
                    )
                else:
                    analysis = analyze_document(
                        source_text,
                        subject,
                        level,
                        duration,
                    )
            except Exception:
                app.logger.exception("Document processing failed")
                error = (
                    "The document could not be processed. "
                    "Please try another PDF or TXT file."
                )

    return render_template(
        "index.html",
        analysis=analysis,
        error=error,
    )


@app.errorhandler(413)
def file_too_large(_error):
    return render_template(
        "index.html",
        analysis=None,
        error="The file is too large. The maximum size is 10 MB.",
    ), 413


if __name__ == "__main__":
    app.run(debug=True)
