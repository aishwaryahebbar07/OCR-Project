# ===================== IMPORTS =====================
import base64
import io
import cv2
import numpy as np
import pytesseract
import re
from datetime import datetime

from dash import Dash, html, dcc, Input, Output, State
from PIL import Image
from pytesseract import Output as TessOutput

# New imports for PDF
from pdf2image import convert_from_bytes

# ===================== APP =====================
app = Dash(__name__)
app.title = "OCR Dashboard"

# ===================== OCR FUNCTION (FOR PDF AND IMAGE) =====================
def extract_text_and_confidence(contents):
    raw_lines = []

    content_type, content_string = contents.split(",")
    content_type = content_type.lower()

    # PDF extraction
    if "pdf" in content_type:
        decoded = base64.b64decode(content_string)

        images = convert_from_bytes(decoded, dpi=120)
        images = images[:1]

        final_lines = []
        raw_lines = []
        confidences = []

        for img in images:

            image_np = np.array(img)
            gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)

            gray = cv2.GaussianBlur(gray, (5, 5), 0)

            gray = cv2.threshold(
                gray, 0, 255,
                cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )[1]

            data = pytesseract.image_to_data(
                gray,
                output_type=TessOutput.DICT,
                config="--oem 3 --psm 6"
            )

            structured = {}

            for i in range(len(data["text"])):
                word = data["text"][i].strip()

                try:
                    conf = float(data["conf"][i])
                except:
                    conf = 0

                if word and conf > 30:
                    block = data["block_num"][i]
                    par = data["par_num"][i]
                    line = data["line_num"][i]

                    structured.setdefault(block, {})
                    structured[block].setdefault(par, {})
                    structured[block][par].setdefault(line, {"words": []})

                    structured[block][par][line]["words"].append(word)

                    confidences.append(conf)
                    
                    
            for block in structured:
                for par in structured[block]:
                    for line_key in structured[block][par]:

                        joined_line = " ".join(
                            structured[block][par][line_key]["words"]
                        )

                        final_lines.append(joined_line)
                        raw_lines.append(joined_line)

                    final_lines.append("")

        text = "\n".join(final_lines).strip()

        confidence = round(sum(confidences)/len(confidences), 2) if confidences else 0

        return text, confidence, raw_lines

    # IMAGE OCR
    decoded = base64.b64decode(content_string)
    image = Image.open(io.BytesIO(decoded))
    print("STEP 2: Image opened successfully")
    image.thumbnail((1200, 1200))
    if image.mode != "RGB":
        image = image.convert("RGB")

    image_np = np.array(image)
    gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    print("STEP 3: Converted to grayscale")

    # Reduce noise
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    # Improve text clarity
    gray = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    print("STEP 4: Starting OCR...")
    data = pytesseract.image_to_data(
        gray,
        output_type=TessOutput.DICT,
        config="--psm 6"
    )
    print("STEP 5: OCR completed")

    structured = {}
    confidences = []

    for i in range(len(data["text"])):
        word = data["text"][i].strip()
        try:
            conf = float(data["conf"][i])
        except:
            conf = 0

        if word and conf > 30:
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
    valid_conf = confidences
    confidence = round(sum(valid_conf) / len(valid_conf), 2) if valid_conf else 0

    return text, confidence

# ===================== DOCUMENT TYPE DETECTION =====================
def detect_document_type(text):
    t = text.lower()

    # Identity Documents
    if any(k in t for k in [
        "aadhaar", "aadhaar card", "pan card",
        "uidai", "date of birth", "dob",
        "passport", "driving licence", "voter id"
    ]):
        return "Identity Document"

    # Resume / CV
    elif any(k in t for k in [
        "resume", "curriculum vitae", "skills",
        "experience", "objective", "projects",
        "technical skills", "internship"
    ]):
        return "Resume / CV"

    # Invoice / Bill
    elif any(k in t for k in [
        "invoice", "gst", "tax invoice",
        "bill no", "total amount", "subtotal",
        "cgst", "sgst", "amount payable"
    ]):
        return "Invoice / Bill"

    # Educational Certificate
    elif any(k in t for k in [
        "certificate", "degree certificate",
        "marks card", "semester", "university",
        "board of examination", "grade sheet"
    ]):
        return "Educational Certificate"

    # Project / Internship Report
    elif any(k in t for k in [
        "project report", "internship report",
        "submitted by", "guided by",
        "department of", "academic year"
    ]):
        return "Project / Academic Report"

    # Research Paper
    elif any(k in t for k in [
        "abstract", "methodology",
        "literature survey", "conclusion",
        "references", "research paper"
    ]):
        return "Research Paper"

    return "General Document"

def highlight_text(text, query):
    if not query:
        return text

    pattern = re.compile(re.escape(query), re.IGNORECASE)
    parts = pattern.split(text)
    matches = pattern.findall(text)

    result = []
    for i, part in enumerate(parts):
        result.append(html.Span(part))
        if i < len(matches):
            result.append(
                html.Mark(matches[i], style={"backgroundColor": "#ffe066"})
            )
    return html.Span(result)


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
                        html.B("Upload Image/PDF")
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
                                    id="file-info",
                                    style={"fontWeight": "600","fontSize": "16px","marginBottom": "10px","color": "#333"}
                                ),

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

                                dcc.Download(id="download-text"),
                                dcc.Store(id="stored-text")

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
    Output("file-info", "children"),
    Output("doc-type", "children"),
    Output("confidence-text", "children"),
    Output("count-text", "children"),
    Output("confidence-bar", "style"),
    Output("file-preview-container", "children"),
    Output("stored-text", "data"),

    Input("upload-image", "contents"),
    
    State("upload-image", "filename"),
)

def update_ui(contents, filename):
    if contents is None:
        return (
            "",   # file-info
            "",   # doc-type
            "",   # confidence-text
            "",   # count-text
            {     # confidence-bar style
                "height": "20px",
                "width": "0%",
                "background": "#2ecc71",
                "transition": "0.6s"
            },
            "",   # preview
            ""    # stored-text
        )
    
    result = extract_text_and_confidence(contents)
    if len(result) == 3:
        text, confidence, raw_lines = result
    else:
        text, confidence = result
        raw_lines = [l for l in text.splitlines() if l.strip()]

    conf_value = confidence if confidence is not None else 0
    conf_value = min(max(conf_value, 0), 100)
    line_count = len(raw_lines)
    word_count = len(re.findall(r'\b\w+\b', text))
    doc_type = detect_document_type(text)
    conf_display = (
    f"{confidence:.2f} %" if confidence is not None else "N/A"
)

    if conf_value >= 80:
        bar_color = "#2ecc71"   # Green
    elif conf_value >= 50:
        bar_color = "#f1c40f"   # Yellow
    else:
        bar_color = "#e74c3c"   # Red

    bar_style = {
        "height": "20px",
        "width": f"{conf_value}%",
        "background": bar_color,
        "transition": "0.6s"
}

    content_type, content_string = contents.split(",")
    current_time = datetime.now().strftime("%d %B %Y, %I:%M %p")

    file_name_display = filename if filename else "Unknown File"

    file_info = (
        f"📄 File Name: {file_name_display}    |    "
        f"🕒 Processed On: {current_time}"
    )

    print("STEP 1: File received")
    print("Content Type:", content_type)

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
        file_info,
        f"📌 Document Type: {doc_type}",
        f"📈 Confidence Score: {conf_display}",
        f"📏 Lines: {line_count}   |   🔤 Words: {word_count}",
        bar_style,
        preview,
        text
    )
@app.callback(
    Output("output-text", "children"),
    Input("stored-text", "data"),
    Input("search-input", "value")
)
def update_search_output(stored_text, search):
    if not stored_text:
        return ""

    return highlight_text(stored_text, search)

# ===================== DOWNLOAD =====================
@app.callback(
    Output("download-text", "data"),
    Input("download-btn", "n_clicks"),
    State("upload-image", "contents"),
    State("confidence-text", "children"),
    prevent_initial_call=True,
)
def download_text(n_clicks, contents, confidence):
    if not contents:
        return None

    result = extract_text_and_confidence(contents)

    if len(result) == 3:
        text, extracted_confidence, raw_lines = result
    else:
        text, extracted_confidence = result

    content = f"{confidence}\n\nExtracted Text:\n{text}"

    return dict(
        content=content,
        filename="ocr_output.txt"
    )

# ===================== RUN =====================
if __name__ == "__main__":
    app.run(debug=False)