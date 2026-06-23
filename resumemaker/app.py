#!/usr/bin/env python3
"""
Resume Tailor AI
────────────────
AI-powered resume customization. Paste a job description, upload your resume,
and get a tailored, ATS-optimized version with a downloadable PDF — in seconds.

Supports: Claude (Anthropic) and OpenAI (GPT-4o)
"""

import gradio as gr
import os
import re
import tempfile
from pathlib import Path

# ─── Optional dependency guards ──────────────────────────────────────────────
try:
    from pdfminer.high_level import extract_text as _pdfminer_extract
    PDFMINER_OK = True
except ImportError:
    PDFMINER_OK = False

try:
    import anthropic
    ANTHROPIC_OK = True
except ImportError:
    ANTHROPIC_OK = False

try:
    from openai import OpenAI
    OPENAI_OK = True
except ImportError:
    OPENAI_OK = False

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable
)


# ─── LLM Prompts ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert resume writer and ATS optimization specialist.

Your task is to tailor the provided resume to better match a specific job description.

STRICT RULES — follow every rule without exception:
1. Preserve the EXACT structure, section order, and layout of the resume
2. ONLY rewrite bullet points under EXPERIENCE and PROJECTS sections
3. Do NOT change: name, contact info, education, certifications, or skills list
4. Naturally embed relevant ATS keywords from the job description into rewrites
5. Do NOT fabricate skills, degrees, companies, or experience the candidate doesn't have
6. Strengthen bullets using action verbs and quantify impact where the original implies it
7. Return ONLY the complete modified resume text — no commentary, no preamble
8. Keep the same bullet symbols (•, -, *) as the original resume
9. Preserve all dates, locations, and company names exactly as written
10. If a section has no bullets (e.g., Education), copy it verbatim"""

USER_PROMPT_TEMPLATE = """JOB DESCRIPTION:
{job_description}

---

ORIGINAL RESUME:
{resume_text}

---

Return the tailored resume below — nothing else."""


# ─── Text Extraction ──────────────────────────────────────────────────────────

def extract_text_from_file(file_path: str) -> str:
    """Extract plain text from a .pdf or .txt file."""
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        if not PDFMINER_OK:
            raise ValueError(
                "pdfminer.six is not installed.\n"
                "Run: pip install pdfminer.six"
            )
        text = _pdfminer_extract(file_path)
        return (text or "").strip()

    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read().strip()

    raise ValueError(f"Unsupported file type '{ext}'. Please upload a .pdf or .txt file.")


# ─── LLM Calls ───────────────────────────────────────────────────────────────

def call_claude(api_key: str, job_desc: str, resume_text: str) -> str:
    """Call Anthropic Claude API to tailor the resume."""
    if not ANTHROPIC_OK:
        raise RuntimeError("anthropic package not installed. Run: pip install anthropic")

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": USER_PROMPT_TEMPLATE.format(
                job_description=job_desc,
                resume_text=resume_text,
            ),
        }],
    )
    return message.content[0].text


def call_openai(api_key: str, job_desc: str, resume_text: str) -> str:
    """Call OpenAI GPT-4o API to tailor the resume."""
    if not OPENAI_OK:
        raise RuntimeError("openai package not installed. Run: pip install openai")

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=4096,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(
                    job_description=job_desc,
                    resume_text=resume_text,
                ),
            },
        ],
    )
    return response.choices[0].message.content


# ─── PDF Generation ───────────────────────────────────────────────────────────

def _build_styles() -> dict:
    """Create a palette of reportlab ParagraphStyles for a clean resume layout."""
    base = dict(fontName="Helvetica", textColor=colors.HexColor("#2d2d2d"))

    return {
        "name": ParagraphStyle(
            "name",
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=26,
            textColor=colors.HexColor("#1a1a2e"),
            spaceAfter=3,
            alignment=TA_CENTER,
        ),
        "contact": ParagraphStyle(
            "contact",
            fontSize=10,
            leading=15,
            textColor=colors.HexColor("#555555"),
            spaceAfter=4,
            alignment=TA_CENTER,
            **{k: v for k, v in base.items() if k != "textColor"},
        ),
        "section": ParagraphStyle(
            "section",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=16,
            textColor=colors.HexColor("#1a1a2e"),
            spaceBefore=8,
            spaceAfter=2,
        ),
        "jobtitle": ParagraphStyle(
            "jobtitle",
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=15,
            textColor=colors.HexColor("#222222"),
            spaceAfter=1,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            leftIndent=14,
            textColor=colors.HexColor("#333333"),
            spaceAfter=2,
        ),
        "body": ParagraphStyle(
            "body",
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#333333"),
            spaceAfter=2,
        ),
    }


def _is_section_header(line: str) -> bool:
    """Return True if the line looks like an all-caps resume section header."""
    s = line.strip()
    return bool(s) and s == s.upper() and len(s) >= 3 and bool(
        re.match(r"^[A-Z][A-Z\s\-/&]+$", s)
    )


def _is_bullet(line: str) -> bool:
    """Return True if the line starts with a bullet symbol."""
    return bool(re.match(r"^\s*[•\-\*◦▪]\s+", line))


def _xml_safe(text: str) -> str:
    """Escape XML special characters for reportlab Paragraph."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text_to_pdf(resume_text: str, output_path: str) -> None:
    """
    Convert plain-text resume to a formatted, readable PDF.

    Strategy:
    - Lines before the first all-caps section header → name + contact block
    - All-caps lines → section headers with a rule
    - Lines starting with •/-/* → indented bullets
    - Lines containing | → job title / company rows (bold)
    - Everything else → body text
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = _build_styles()
    story: list = []
    lines = resume_text.splitlines()

    # Find index of first section header to isolate the header block
    first_section = next(
        (i for i, ln in enumerate(lines) if _is_section_header(ln)),
        len(lines),
    )

    # ── Render resume header (name + contact) ────────────────────────────────
    header_lines = [ln.strip() for ln in lines[:first_section] if ln.strip()]
    for j, hline in enumerate(header_lines):
        style = styles["name"] if j == 0 else styles["contact"]
        story.append(Paragraph(_xml_safe(hline), style))
    if header_lines:
        story.append(Spacer(1, 6))

    # ── Render body sections ──────────────────────────────────────────────────
    for line in lines[first_section:]:
        stripped = line.strip()

        if not stripped:
            story.append(Spacer(1, 3))
            continue

        safe = _xml_safe(stripped)

        if _is_section_header(stripped):
            story.append(Paragraph(safe, styles["section"]))
            story.append(HRFlowable(
                width="100%",
                thickness=0.75,
                color=colors.HexColor("#1a1a2e"),
                spaceAfter=4,
            ))
            continue

        if _is_bullet(line):
            bullet_content = re.sub(r"^\s*[•\-\*◦▪]\s+", "", line).strip()
            story.append(Paragraph(f"• {_xml_safe(bullet_content)}", styles["bullet"]))
            continue

        # Lines with | separator → job title / company / date row
        if "|" in stripped:
            story.append(Paragraph(safe, styles["jobtitle"]))
            continue

        story.append(Paragraph(safe, styles["body"]))

    doc.build(story)


# ─── Main Pipeline ────────────────────────────────────────────────────────────

def generate_resume(
    api_provider: str,
    api_key: str,
    job_description: str,
    resume_file,       # filepath string from gr.File, or None
    resume_text_input: str,
) -> tuple[str, str | None, str]:
    """
    End-to-end pipeline:
      1. Validate inputs
      2. Extract resume text (file takes priority over pasted text)
      3. Call the selected LLM
      4. Generate PDF from the tailored text
      Returns (tailored_text, pdf_path_or_None, status_message)
    """
    # Validate
    if not api_key or not api_key.strip():
        return "", None, "❌ Please enter your API key."
    if not job_description or not job_description.strip():
        return "", None, "❌ Please paste a job description."

    # Extract resume text
    resume_text = ""
    if resume_file is not None:
        file_path = resume_file if isinstance(resume_file, str) else resume_file.name
        try:
            resume_text = extract_text_from_file(file_path)
        except Exception as exc:
            return "", None, f"❌ File error: {exc}"

    if not resume_text and resume_text_input and resume_text_input.strip():
        resume_text = resume_text_input.strip()

    if not resume_text:
        return "", None, "❌ Please upload a resume file or paste resume text."

    # Call LLM
    try:
        if api_provider == "Claude (Anthropic)":
            tailored = call_claude(api_key.strip(), job_description.strip(), resume_text)
        else:
            tailored = call_openai(api_key.strip(), job_description.strip(), resume_text)
    except Exception as exc:
        return "", None, f"❌ LLM error: {exc}"

    # Generate PDF
    try:
        tmp = tempfile.NamedTemporaryFile(
            delete=False, suffix=".pdf", prefix="tailored_resume_"
        )
        tmp.close()
        text_to_pdf(tailored, tmp.name)
        return tailored, tmp.name, "✅ Done! Edit the preview if needed, then click Download PDF."
    except Exception as exc:
        return tailored, None, f"⚠️ Resume tailored but PDF failed: {exc}"


def rebuild_pdf(resume_text: str) -> tuple:
    """Regenerate PDF from the (possibly edited) preview text."""
    if not resume_text or not resume_text.strip():
        return gr.update(visible=False), None, "❌ No text to convert."
    try:
        tmp = tempfile.NamedTemporaryFile(
            delete=False, suffix=".pdf", prefix="tailored_resume_"
        )
        tmp.close()
        text_to_pdf(resume_text, tmp.name)
        return gr.update(value=tmp.name, visible=True), tmp.name, "✅ PDF ready — click the file to download."
    except Exception as exc:
        return gr.update(visible=False), None, f"❌ PDF error: {exc}"


# ─── Example Data ─────────────────────────────────────────────────────────────

EXAMPLE_JOB = """Senior Software Engineer — Backend (Python)

We are looking for a Senior Backend Engineer to join our growing platform team.

Responsibilities:
- Design and build scalable REST APIs using Python (FastAPI / Django)
- Own PostgreSQL schema design, query tuning, and Redis caching strategies
- Lead code reviews, set engineering standards, and mentor junior engineers
- Build and maintain CI/CD pipelines with GitHub Actions and Docker
- Collaborate across engineering, product, and data teams in an Agile environment

Requirements:
- 5+ years of Python backend development
- Strong SQL skills (PostgreSQL preferred)
- Experience with Docker, Kubernetes, and AWS (EC2, RDS, S3, Lambda)
- Microservices and distributed systems experience
- Excellent written communication and cross-team collaboration skills"""

EXAMPLE_RESUME = """Jane Doe
jane.doe@email.com | linkedin.com/in/janedoe | (415) 555-0192 | San Francisco, CA

SUMMARY
Software engineer with 6 years of experience building backend services and web applications.

EXPERIENCE

Software Engineer | TechCorp Inc. | March 2021 – Present
• Built internal web applications using Python and JavaScript
• Helped improve database query performance across several services
• Participated in weekly code reviews with the engineering team
• Deployed applications to cloud infrastructure using basic CI/CD scripts

Junior Developer | StartupXYZ | June 2018 – Feb 2021
• Developed new features for the main product using Python and Flask
• Wrote unit tests and fixed bugs reported by QA
• Worked in a small agile team and contributed to sprint planning

PROJECTS

Internal Analytics Dashboard
• Built a data dashboard using Python, Pandas, and Plotly for the ops team

Personal Portfolio Website
• Deployed a portfolio site using Flask on Heroku with a PostgreSQL backend

EDUCATION

B.S. Computer Science | UC Berkeley | May 2018

SKILLS
Python, JavaScript, SQL, PostgreSQL, Flask, Django, Git, Docker, AWS, REST APIs, Redis"""


# ─── Gradio UI ────────────────────────────────────────────────────────────────

CUSTOM_CSS = """
.gradio-container { max-width: 1280px !important; margin: auto; }
footer { display: none !important; }
"""

def build_ui() -> gr.Blocks:
    with gr.Blocks(
        title="Resume Tailor AI",
        theme=gr.themes.Soft(primary_hue="blue", neutral_hue="slate"),
        css=CUSTOM_CSS,
    ) as demo:

        gr.Markdown("""
        # 📄 Resume Tailor AI
        **Customize your resume for any job description in seconds — ATS-optimized, no hallucinations.**
        """)

        with gr.Row(equal_height=False):

            # ── LEFT: Inputs ──────────────────────────────────────────────────
            with gr.Column(scale=1, min_width=400):
                gr.Markdown("### ⚙️ API Configuration")
                api_provider = gr.Dropdown(
                    label="LLM Provider",
                    choices=["Claude (Anthropic)", "OpenAI (GPT-4o)"],
                    value="Claude (Anthropic)",
                )
                api_key = gr.Textbox(
                    label="API Key",
                    placeholder="sk-ant-...  or  sk-...",
                    type="password",
                )

                gr.Markdown("### 📋 Job Description")
                job_desc_input = gr.Textbox(
                    label="Paste the full job description",
                    placeholder=EXAMPLE_JOB,
                    lines=11,
                )

                gr.Markdown("### 📎 Your Resume")
                with gr.Tabs():
                    with gr.Tab("Upload File"):
                        resume_file_input = gr.File(
                            label="Drop a .pdf or .txt file here",
                            file_types=[".pdf", ".txt"],
                            type="filepath",
                        )
                    with gr.Tab("Paste Text"):
                        resume_text_input = gr.Textbox(
                            label="Or paste resume text directly",
                            placeholder=EXAMPLE_RESUME,
                            lines=18,
                        )

                with gr.Row():
                    generate_btn = gr.Button(
                        "🚀 Generate Tailored Resume", variant="primary", scale=3
                    )
                    example_btn = gr.Button("📌 Load Example", scale=1)

            # ── RIGHT: Output ─────────────────────────────────────────────────
            with gr.Column(scale=1, min_width=400):
                gr.Markdown("### 📝 Tailored Resume Preview")
                status_box = gr.Textbox(
                    label="Status", interactive=False, lines=1, max_lines=2
                )
                output_preview = gr.Textbox(
                    label="Preview (you can edit this before downloading)",
                    lines=25,
                    interactive=True,
                    show_copy_button=True,
                )
                download_btn = gr.Button("📥 Download as PDF", variant="secondary")
                pdf_file_output = gr.File(
                    label="Your Tailored Resume PDF",
                    visible=False,
                )

        gr.Markdown(
            "> 🔒 **Privacy**: Your API key and resume are processed locally "
            "and sent only to the LLM provider you selected. Nothing is stored."
        )

        # Internal state: holds the generated PDF path
        _pdf_state = gr.State(None)

        # ── Event wiring ──────────────────────────────────────────────────────

        def on_generate(provider, key, jd, r_file, r_text):
            text, pdf_path, msg = generate_resume(provider, key, jd, r_file, r_text)
            return text, pdf_path, msg

        generate_btn.click(
            fn=on_generate,
            inputs=[api_provider, api_key, job_desc_input, resume_file_input, resume_text_input],
            outputs=[output_preview, _pdf_state, status_box],
        )

        download_btn.click(
            fn=rebuild_pdf,
            inputs=[output_preview],
            outputs=[pdf_file_output, _pdf_state, status_box],
        )

        def load_examples():
            return EXAMPLE_JOB, None, EXAMPLE_RESUME

        example_btn.click(
            fn=load_examples,
            outputs=[job_desc_input, resume_file_input, resume_text_input],
        )

    return demo


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    demo = build_ui()
    print("\n✅ Resume Tailor AI is starting...")
    print("   Open your browser at: http://localhost:7860\n")
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_api=False,
    )
