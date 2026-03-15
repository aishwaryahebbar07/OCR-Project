# ===================== IMPORTS =====================
import base64
import io
import cv2
import numpy as np
import pytesseract
import re

from dash import Dash, html, dcc, Input, Output, State
from PIL import Image
from pytesseract import Output as TessOutput

# New imports for PDF, DOCX, TXT
from PyPDF2 import PdfReader
from docx import Document

# ===================== APP =====================
app = Dash(__name__)
app.title = "OCR Dashboard"

# ===================== OCR FUNCTION (EXTENDED FOR PDF, DOCX, TXT) =====================
def extract_text_and_confidence(contents):
    content_type, content_string = contents.split(",")
    content_type = content_type.lower()

    # PDF extraction
    if "pdf" in content_type:
        decoded = base64.b64decode(content_string)
        reader = PdfReader(io.BytesIO(decoded))
        lines = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                lines.extend(text.splitlines())
        return "\n".join(lines).strip(), 100

    # DOCX extraction
    if "word" in content_type or "docx" in content_type:
        decoded = base64.b64decode(content_string)
        doc = Document(io.BytesIO(decoded))
        lines = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(lines).strip(), 100

    # TXT extraction
    if "text" in content_type:
        decoded = base64.b64decode(content_string)
        text = decoded.decode("utf-8", errors="ignore")
        return text.strip(), 100

    # IMAGE OCR
    decoded = base64.b64decode(content_string)
    image = Image.open(io.BytesIO(decoded))
    if image.mode != "RGB":
        image = image.convert("RGB")

    image_np = np.array(image)
    gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)

    data = pytesseract.image_to_data(
        gray,
        output_type=TessOutput.DICT,
        config="--psm 6"
    )

    structured = {}
    confidences = []

    for i in range(len(data["text"])):
        word = data["text"][i].strip()
        conf = int(data["conf"][i])

        if word and conf > 0:
            block = data["block_num"][i]
            par = data["par_num"][i]
            line = data["line_num"][i]
            top = data["top"][i]

            structured.setdefault(block, {})
            structured[block].setdefault(par, {})
            structured[block][par].setdefault(line, {"top": top, "words": []})

            structured[block][par][line]["words"].append(word)
            confidences.append(conf)

    final_lines = []

    for block in sorted(structured):
        for par in sorted(structured[block]):
            lines = structured[block][par]
            for line_key in sorted(lines, key=lambda x: lines[x]["top"]):
                final_lines.append(" ".join(lines[line_key]["words"]))
            final_lines.append("")  # paragraph spacing

    text = "\n".join(final_lines).strip()
    confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0

    return text, confidence

# ===================== DOCUMENT TYPE DETECTION =====================
def detect_document_type(text):
    t = text.lower()
    if any(k in t for k in ["aadhaar card", "pan card", "uidai", "dob"]):
        return "Identity Document"
    if any(k in t for k in ["certificate", "degree", "university", "college"]):
        return "Educational Certificate"
    if any(k in t for k in ["invoice", "gst", "total", "amount", "tax"]):
        return "Invoice / Bill"
    if any(k in t for k in ["resume", "skills", "experience", "education"]):
        return "Resume / CV"
    return "General Document"

def highlight_text(text, query):
    if not query:
        return text

    pattern = re.compile(re.escape(query), re.IGNORECASE)
    parts = pattern.split(text)
    matches = pattern.findall(text)

    result = []
    for i, part in enumerate(parts):
        result.append(part)
        if i < len(matches):
            result.append(
                html.Mark(matches[i], style={"backgroundColor": "#ffe066"})
            )
    return result


# ===================== LAYOUT =====================
app.layout = html.Div(
    style={
        "minHeight": "100vh",
        "background": "linear-gradient(120deg, #667eea, #764ba2)",
        "padding": "50px",
        "fontFamily": "Poppins, Segoe UI"
    },
    children=[

        html.Div(
            style={
                "maxWidth": "1200px",
                "margin": "auto",
                "background": "rgba(255,255,255,0.95)",
                "borderRadius": "20px",
                "padding": "35px",
                "boxShadow": "0 20px 45px rgba(0,0,0,0.25)"
            },
            children=[

                html.Div(
                    style={"textAlign": "center", "marginBottom": "35px"},
                    children=[
                        html.H1("📄 OptiScan OCR", style={"color": "#2c3e50", "fontweight":"700"}),
                        html.P(
                            html.I("An OCR-Based Intelligent Text Extraction and Analysis System"),
                            style={"color": "#555", "fontSize": "17px"}
                        )
                    ]
                ),

                dcc.Upload(
                    id="upload-image",
                    children=html.Div([
                        html.I("📤 ", style={"fontSize": "26px"}),
                        html.B("Upload Image/PDF/Docx/TXT")
                    ]), 
                    style={
                        "width": "100%",
                        "height": "100px",
                        "lineHeight": "100px",
                        "borderWidth": "3px",
                        "borderStyle": "dashed",
                        "borderRadius": "15px",
                        "textAlign": "center",
                        "background": "#eef1f6",
                        "cursor": "pointer",
                        "marginBottom": "35px",
                        "boxShadow": "0 8px 20px rgba(0,0,0,0.08)" 

                    },
                    multiple=False,
                ),
                dcc.Input(
    id="search-input",
    type="text",
    placeholder="🔍 Search word in document...",
    style={
        "width": "98%",
        "padding": "12px",
        "borderRadius": "12px",
        "border": "1px solid #ccc",
        "marginBottom": "35px"
    }
),

                html.Div(
                    style={"display": "flex", "gap": "30px"},
                    children=[

                        html.Div(
                            style={
                                "width": "35%",
                                "backgroundImage": "linear-gradient(to bottom, #f4f6f8 0%, #e9edf2 100%)",
                                "borderRadius": "15px",
                                "padding": "18px",
                                "boxShadow": "0 20px 40px rgba(0,0,0,0.15)",
                                "textAlign": "center"
                            },
                            children=[
                                html.H4("📂 Uploaded File Preview"),
                                html.Div(
                                    id="file-preview-container",
                                    style={"width": "100%", "height": "300px", "borderRadius": "10px"}
                                )
                            ]
                        ),

                        html.Div(
                            style={
                                "width": "65%",
                                "backgroundImage": "linear-gradient(to bottom, #f7f8fa 0%, #eff2f6 100%)",
                                "borderRadius": "15px",
                                "padding": "18px",
                                "boxShadow": "0 15px 35px rgba(0,0,0,0.15)"
                            },
                            children=[

                                html.Div(
                                    id="doc-type",
                                    style={"fontWeight": "700", "fontSize": "18px", "marginBottom": "10px"}
                                ),

                                html.Div(
                                    id="confidence-text",
                                    style={"fontWeight": "600", "marginBottom": "8px"}
                                ),

                                html.Div(
                                     id="count-text",
                                    style={
                                        "fontWeight": "500",
                                        "marginBottom": "12px",
                                        "color": "#444"
                                    }
                               ),


                                html.Div(
                                    style={
                                        "background": "#e0e0e0",
                                        "borderRadius": "10px",
                                        "overflow": "hidden",
                                        "marginBottom": "18px"
                                    },
                                    children=[
                                        html.Div(
                                            id="confidence-bar",
                                            style={
                                                "height": "20px",
                                                "width": "0%",
                                                "background": "#2ecc71",
                                                "transition": "0.6s"
                                            }
                                        )
                                    ]
                                ),

                                dcc.Tabs(
                                    children=[

                                        dcc.Tab(
                                            label="Extracted Text",
                                            children=[
                                                html.Pre(
                                                    id="output-text",
                                                    style={
                                                        "whiteSpace": "pre-wrap",
                                                        "height": "260px",
                                                        "overflowY": "auto",
                                                        "background": "#f9f9f9",
                                                        "padding": "12px",
                                                        "borderRadius": "8px",
                                                        "border":"1px solid #e0e0e0"
                                                    }
                                                )
                                            ]
                                        )
                                    ]
                                ),

                                html.Br(),

                                html.Button(
                                    "⬇ Download Output",
                                    id="download-btn",
                                    style={
                                        "background": "linear-gradient(90deg, #667eea, #764ba2)",
                                        "color": "white",
                                        "border": "none",
                                        "padding": "12px 22px",
                                        "borderRadius": "25px",
                                        "cursor": "pointer",
                                        "fontWeight": "600"
                                    }
                                ),

                                dcc.Download(id="download-text")
                            ]
                        )
                    ]
                )
            ]
        )
    ]
)

# ===================== CALLBACK =====================
@app.callback(
    Output("doc-type", "children"),
    Output("output-text", "children"),
    Output("confidence-text", "children"),
    Output("count-text", "children"),
    Output("confidence-bar", "style"),
    Output("file-preview-container", "children"),
    Input("upload-image", "contents"),
    Input("search-input", "value"),

)
def update_ui(contents , search):
    if contents is None:
        return "", "", "", {"width": "0%", "background": "#2ecc71"}, ""

    text, confidence = extract_text_and_confidence(contents)
    lines = [l for l in text.splitlines() if l.strip()]
    line_count = len(lines)
    word_count = len(re.findall(r'\b\w+\b', text))
    display_text = highlight_text(text, search)
    doc_type = detect_document_type(text)

    bar_style = {
        "height": "20px",
        "width": f"{confidence}%",
        "background": "#2ecc71",
        "transition": "0.6s"
    }

    content_type, content_string = contents.split(",")

    # Generic preview for all file types
    if content_type.startswith("data:image"):
        preview = html.Img(
            src=contents,
            style={"width": "100%", "height": "100%", "borderRadius": "10px", "objectFit": "contain"}
        )
    elif content_type.startswith("data:application/pdf"):
        preview = html.Iframe(
            src=contents,
            style={"width": "100%", "height": "100%", "borderRadius": "10px"}
        )
    elif content_type.startswith("data:application/vnd.openxmlformats-officedocument.wordprocessingml.document") \
            or content_type.startswith("data:text/plain"):
        html_content = f"<pre style='font-family:monospace; white-space: pre-wrap;'>{text}</pre>"
        html_base64 = "data:text/html;base64," + base64.b64encode(html_content.encode()).decode()
        preview = html.Iframe(
            src=html_base64,
            style={"width": "100%", "height": "100%", "borderRadius": "10px"}
        )
    else:
        preview = html.Div("Cannot preview this file type.", style={"padding": "20px", "color": "red"})

    return (
        f"📌 Document Type: {doc_type}",
        display_text,
        f"Confidence Score: {confidence} %",
        f"📄 Lines: {line_count}   |   🔤 Words: {word_count}",
        bar_style,
        preview
    )

# ===================== DOWNLOAD =====================
@app.callback(
    Output("download-text", "data"),
    Input("download-btn", "n_clicks"),
    State("output-text", "children"),
    State("confidence-text", "children"),
    prevent_initial_call=True,
)
def download_text(n_clicks, text, confidence):
    if not text:
        return None
    content = f"{confidence}\n\nExtracted Text:\n{text}"
    return dict(content=content, filename="ocr_output.txt")

# ===================== RUN =====================
if __name__ == "__main__":
    app.run(debug=False)