"""Build the downloadable CV PDF (assets/Chaeyoon_Kim_CV.pdf).

The content mirrors cv.html, so update both when the CV changes.

Usage (from the repository root):
    pip install reportlab
    python scripts/build_cv.py              # writes assets/Chaeyoon_Kim_CV.pdf
    python scripts/build_cv.py out.pdf      # writes to another path
"""
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable, KeepTogether, CondPageBreak)

INK = HexColor("#111111")
RULE = HexColor("#333333")
LINK = HexColor("#1a4fa0")
M = 56.69291  # 2 cm

name = ParagraphStyle("name", fontName="Helvetica-Bold", fontSize=24, leading=28,
                      alignment=TA_CENTER, textColor=INK)
contact = ParagraphStyle("contact", fontName="Helvetica", fontSize=9.5, leading=13,
                         alignment=TA_CENTER, textColor=INK)
summary = ParagraphStyle("summary", fontName="Helvetica", fontSize=9.7, leading=13.2,
                         alignment=TA_JUSTIFY, textColor=INK)
section = ParagraphStyle("section", fontName="Helvetica-Bold", fontSize=11.5, leading=14,
                         textColor=INK)
head = ParagraphStyle("head", fontName="Helvetica-Bold", fontSize=10, leading=13,
                      textColor=INK)
head_r = ParagraphStyle("head_r", parent=head, alignment=TA_RIGHT)
sub = ParagraphStyle("sub", fontName="Helvetica-Bold", fontSize=9.6, leading=13,
                     textColor=INK, spaceBefore=4, spaceAfter=1)
bullet = ParagraphStyle("bullet", fontName="Helvetica", fontSize=9.4, leading=12.6,
                        textColor=INK, leftIndent=12, bulletIndent=0,
                        bulletFontName="Helvetica", bulletFontSize=10, spaceAfter=3)
plain = ParagraphStyle("plain", fontName="Helvetica", fontSize=9.4, leading=12.6,
                       textColor=INK, spaceAfter=4)

W = A4[0] - 2 * M
story = []


def link(text, url):
    return f'<link href="{url}"><font color="#1a4fa0">{text}</font></link>'


def sec(title):
    story.append(CondPageBreak(90))
    story.append(Spacer(1, 8))
    story.append(Paragraph(title, section))
    story.append(HRFlowable(width="100%", thickness=1, color=RULE, spaceBefore=1, spaceAfter=6))


def entry(title, dates, bullets):
    t = Table([[Paragraph(title, head), Paragraph(dates, head_r)]],
              colWidths=[362.14, W - 362.14])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LINEBELOW", (0, 0), (-1, -1), 0.75, RULE),
    ]))
    first = [t, Spacer(1, 2)] + ([Paragraph(bullets[0], bullet, bulletText="-")] if bullets else [])
    story.append(KeepTogether(first))
    for b in bullets[1:]:
        story.append(Paragraph(b, bullet, bulletText="-"))
    story.append(Spacer(1, 1))


def b(label, text):
    return f"<b>{label}</b> {text}"


story.append(Paragraph("Chaeyoon Kim", name))
story.append(Spacer(1, 2))
story.append(Paragraph(
    f'{link("chaeyoonakim@gmail.com", "mailto:chaeyoonakim@gmail.com")}&nbsp;&nbsp;|&nbsp;&nbsp;'
    f'+44 (0) 7856231406&nbsp;&nbsp;|&nbsp;&nbsp;LinkedIn {link("@chaeyoonakim", "https://www.linkedin.com/in/chaeyoonakim")}'
    f'&nbsp;&nbsp;|&nbsp;&nbsp;GitHub {link("@chaeyoonakim", "https://github.com/chaeyoonakim")}', contact))
story.append(Spacer(1, 14))
story.append(Paragraph(
    "Certified AI Ethicist and Data Scientist with about 5 years of UK public sector experience, following 6.5 years "
    "in semiconductor engineering at Samsung Electronics. Specialised in large-scale analytics, AI "
    "engineering, and healthcare workforce modeling. Proven track record of building LLM-powered applications in "
    "Python and PySpark, while leading reproducible, secure analytics engineering for the NHS workforce across England.",
    summary))

sec("EXPERIENCE")
entry("Data Scientist – NHS England (London, UK)", "Apr 2024 – Present", [
    "Redesigned the CT1 training-place allocation methodology from a weighted multi-criteria model into a rule-based "
    "model using Python and Excel, presenting Tableau outputs that informed prioritisation for under-doctored "
    "deaneries during 2024 BMA industrial action negotiations.",
    "Lead Developer for the 10-Year Workforce Plan modelling under NHS England’s Business Critical Model (BCM) "
    "governance: validating the model’s key assumptions in Python and PySpark, working with Department of Health "
    "and Social Care and NHS England policy leads to shape the response to National Audit Office recommendations, "
    "and presenting model components to the External Scrutiny Panel.",
    "Manage the project’s dedicated Azure Data Lake Storage (ADLS Gen2) and Databricks clusters, coordinating with "
    "UDAL Data Engineers on secure environments; co-led the migration of legacy PySpark pipelines off deprecated DBFS "
    "onto Entra-secured Data Lake containers and coordinated Windows 11 migration testing to protect model continuity.",
    "Led the transition of legacy Excel workforce models into automated Databricks and Python pipelines with "
    "documented assumptions, strengthened data lineage and peer-reviewed Git version control; refactored the Python "
    "codebase to cut model runtime by around half and enable cross-functional teams to extend it.",
    "As Community Pharmacy modelling workstream lead, coordinated a dozen stakeholder groups — including "
    "pharmacy Deans and Chief Pharmaceutical Officers — into a single delivery scope; launched a Pythonised "
    "supply-and-demand model within six months, secured the model SRO’s approval despite late changes to "
    "baseline and counterfactual assumptions, and presented it at the national consultation on Community Pharmacy "
    "workforce interventions.",
    "Designed an NLTK-based sentiment-analysis pipeline for the Reporting, Insights, Publications and Transparency "
    "programme and contributed to a paper on insights maturity for the CEO’s office and Board; applied NLP and "
    "sentiment analysis to meeting transcripts to assess staff views on organisational change and "
    "internal AI adoption.",
    "Conduct horizon scanning of emerging data and AI engineering practice, including exploratory research into "
    "AI-enabled gains in workforce productivity.",
    "Providing Databricks, Python and Git training and onboarding to analysts and new data scientists, promoting "
    "coding best practices across the modelling team.",
])
entry("Junior Data Scientist – Health Education England (London, UK)", "Jun 2022 – Mar 2024", [
    "Maintained a pythonised geo-spatial analysis and produced Tableau dashboards analysing clinical placement "
    "capacity, workforce supply trends and geographic demand across 65 medical specialties for the HEE Board’s "
    "tariff-funding review, advising medical Deans on redistributing specialty training posts and informing NHS "
    "England’s recommendations to the Office for Students on new dental school places.",
    "Supported R programming capability to predict a complex birth delivery on planning maternity labour services, "
    "with source data from Royal College of Obstetricians and Gynaecologists (RCOG) statisticians.",
    "Collaborated with Data Engineering and Product teams using Jira/Agile framework to manage project timelines.",
])
entry("Data Manager – UCL Great Ormond Street Institute of Child Health (London, UK)", "Apr 2022 – Jun 2022", [
    "Collaborated with bioinformaticians and statisticians on the GSK Sotrovimab Covid-19 study, cleaning and "
    "transforming lab data.",
    "Designed a MySQL server for secure data transfers from entry points.",
])
entry("Engineer – Samsung Electronics, Foundry Business (Gyeonggi-do, South Korea)", "Jul 2011 – Jan 2018", [
    "Operated Chemical Vapour Deposition (CVD) equipment in 24/7 shift operations for high-volume 32/28nm and "
    "14/10nm semiconductor production, and supported set-up and ramp-up of a new 7/10nm line.",
    "Established maintenance SOPs and data-driven part-replacement criteria by evaluating correlations between "
    "plasma process parameters and component condition.",
    "Derived optimal process conditions through simulation built on deposition and clean measurements, suppressing "
    "particle generation and improving yield.",
    "Owned equipment asset and standards management on the Equipment Engineering System (EES): built gas and "
    "chemical usage metering and monitoring that detected unnecessary utility consumption and cut costs; "
    "with EES Master privileges, configured thin-film unit-process alarms and implemented Tool-to-Tool "
    "Matching (TTTM).",
])

sec("PROJECTS")
story.append(Paragraph("Strategic planning:", sub))
story.append(Paragraph(b("10-Year Workforce Plan modelling:",
    "Working with a multidisciplinary group to refresh and refine the NHS Long-Term Workforce Plan modelling "
    "(published in Jun 2022), incorporating National Audit Office feedback."), bullet, bulletText="-"))
story.append(Paragraph("AI &amp; Machine Learning engineering:", sub))
for lbl, txt in [
    (link("Endo Loop:", "https://engine-ai-hackathon-frontend.vercel.app/"), "Co-built a non-diagnostic, at-home pattern journal for endometriosis and chronic pelvic pain, "
     "combining voice or manual symptom logs with wearable signals in a deterministic, safety-guarded pattern "
     "engine; awarded joint 5th place at the eMed and OpenAI Reimagine Health "
     "hackathon (Jul 2026)."),
    (link("NoteGuard:", "https://huggingface.co/spaces/chaeyoona/noteguard-agent"), "Built a trust layer for clinical AI: a LangGraph agent that de-identifies NHS "
     "clinical free-text before any model sees it, so an LLM can safely draft discharge summaries with a measured "
     "residual-PII trust score; built at the {Tech: Europe} London AI Hackathon (Jun 2026)."),
    (link("NHS Policy Navigator:", "https://nhs-policy-navigator.vercel.app/"), "Built an adaptive Retrieval-Augmented Generation pipeline over the published 10-Year "
     "Health Plan and public NHS news feeds at the MongoDB Agentic Evolution Hackathon (May 2026), then refined it "
     "with a working group through a spec-driven development cycle at near-zero infrastructure cost."),
    ("Pharmacy First agent:", "Presented an LLM-powered analysis about NHS Pharmacy operation with open source "
     "at PyConUK, NHS RPySOC conference, and Health and Care Analytics (HACA) conference 2025."),
    ("Reducing the missed NHS appointments:", "Proposed a ML solution to reduce the millions costs and increasing "
     "waitlists for a hackathon challenge set by the Number 10 Downing Street data science team (Sep 2025)."),
    ("AI for NHS Healthcare professionals:", "Co-developed a multilingual “NHS Career Coach” on Azure AI Foundry "
     "that retrieves and cites Health Education England careers content and adapts its guidance to user personas; "
     "awarded 2nd place at the NHS England, Microsoft and Kainos Hack for Health hackathon (Nov 2024)."),
    ("Integrated Operational Pressures Escalation Level (OPEL) prediction:", "Demonstrated ML models on NHS "
     "Federated Data Platform during a hackathon operated by Palantir Technologies and KPMG (Nov 2024)."),
]:
    story.append(Paragraph(b(lbl, txt), bullet, bulletText="-"))
story.append(Paragraph("Teaching and outreach:", sub))
story.append(Paragraph(b("AI Engineering training programme:",
    "Designed and delivered a training programme for learners from undergraduates to NHS analysts and clinicians, "
    "teaching reproducible software engineering, responsible AI and governance principles using open-source NHS "
    "datasets; accepted as a peer-reviewed oral presentation in computer science education."), bullet, bulletText="-"))
story.append(Paragraph("Research and publication:", sub))
story.append(Paragraph(
    "Developed R and Python conversion code for a textbook, &lt;Foundations of Programming, Statistics, and Machine "
    "Learning for Business Analytics&gt; (published in Apr 2023), then co-authored a translated edition in Korean "
    "(published in Feb 2025).", bullet, bulletText="-"))
story.append(Paragraph(
    "Kim, C. and Jiménez-Ruiz, E. (2022) "
    f"{link('CitySAT: a System for the Semantic Answer Type Prediction Task', 'https://ceur-ws.org/Vol-3119/paper8.pdf')}. "
    "CEUR Workshop Proceedings, Vol. 3119 (SMART 2021, ISWC Semantic Web Challenge), pp. 77–88. First author.",
    bullet, bulletText="-"))

sec("EDUCATION")
entry("MSc Data Science (Distinction) – City St George’s, University of London (London, UK)",
      "Sep 2020 – Oct 2021", [
    "Ranked 1st on the global leaderboard of the International Semantic Web Conference (ISWC) 2021 SMART Challenge "
    "as a sole entrant with CitySAT, a two-stage hybrid system using Logistic Regression for answer category and "
    "literal types and a Multi-Layer Perceptron over ~760 DBpedia ontology classes; achieved 98.4% accuracy and "
    "84.2% NDCG@5 on the official test set, and delivered an oral presentation and a poster at ISWC in October 2021.",
])
entry("PGCert. Data Analytics – University of Sheffield (Sheffield, UK)", "Sep 2018 – Jul 2020", [
    b("Modules include", "Computer Security and Forensics, Machine Learning and Adaptive Intelligence, Statistical "
      "Data Science in R."),
])
entry("BSc Electronic Engineering – Kyungpook National University (Daegu, South Korea)", "Mar 2007 – Aug 2011", [
    b("Modules include", "Electronic Engineering Lab (MATLAB), Calculus, Numerical Analysis."),
])
sec("CERTIFICATIONS")
entry("Certified AI Ethicist (CAIE) – oxethica", "Apr 2026", [
    f"Certified by oxethica ({link('credential', 'https://www.virtualbadge.io/certificate-validator?credential=1e3d9a6e-545f-43de-b0e3-8bd943998155')}).",
])
entry("Oxford AI Ethics, Regulation and Compliance Programme – Saïd Business School, University of Oxford",
      "Mar 2026", [
    f"Completed the programme ({link('credential', 'https://certify.sbs.ox.ac.uk/22a357d7-9ddb-483c-bdf4-9cf8ed2d355f')}); published the reflective article "
    f"“{link('Stepping back from my technical day-to-day and into history, philosophy and regulation', 'https://www.sbs.ox.ac.uk/oxford-experience/blogs/chaeyoon-kim/stepping-back-my-technical-day-day-and-history-philosophy-and-regulation')}” "
    "on the Saïd Business School Oxford Experience blog.",
])

sec("VOLUNTEERING")
story.append(Paragraph(b("The UK-Korea Global Health Forum working group:",
    "organised a conference with senior researchers at the London School of Hygiene &amp; Tropical Medicine (LSHTM)."),
    plain))
story.append(Paragraph(b("Professional Mentor at the University of Greenwich, and City St George’s, University of London:",
    "supported early career interview preparation for 3+ years; recognised at City St George’s 2025 Professional "
    f"Mentoring Awards and featured in the alumni article “{link('A great mentor is both generous and curious', 'https://blogs.city.ac.uk/city-alumni/2025/10/28/celebrating-professional-mentoring-a-great-mentor-is-both-generous-and-curious/')}”."), plain))
story.append(Paragraph(b("Global Ambassador at LangChain:",
    "hosted technical meetups and organised a hackathon in central London; collaborated with AI builder "
    "communities across North and South America (including Halifax and Buenos Aires) in 2025, and with engineering "
    "communities across Europe (including Amsterdam, Munich, Zurich, Stockholm and Paris) in 2026."), plain))
story.append(Paragraph(b("Conference and community organiser:",
    "volunteered at PyCon UK and other leading UK technology conferences; planned or helped run local meetups "
    "ranging from 50 to 600+ attendees."), plain))

out = sys.argv[1] if len(sys.argv) > 1 else "assets/Chaeyoon_Kim_CV.pdf"
doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=M - 6, rightMargin=M - 6,
                        topMargin=M * 0.75 - 6, bottomMargin=M * 0.75 - 6,
                        title="Chaeyoon Kim - CV", author="Chaeyoon Kim")
doc.build(story)
