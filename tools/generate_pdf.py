import argparse
import json
import os
import sys
from markdown import markdown
from xhtml2pdf import pisa

def convert_md_to_pdf(input_path, output_path):
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Markdown file not found at '{input_path}'")

    with open(input_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    html_body = markdown(md_content)
    html_doc = f"""
    <html>
    <head>
    <style>
        @page {{ size: A4; margin: 2cm; }}
        body {{ font-family: Helvetica, Arial, sans-serif; font-size: 11pt; color: #333333; line-height: 1.4; }}
        h1 {{ font-size: 20pt; color: #111111; margin-bottom: 0px; }}
        h2 {{ font-size: 14pt; color: #222222; border-bottom: 1px solid #cccccc; padding-bottom: 3px; margin-top: 15px; }}
        h3 {{ font-size: 12pt; color: #444444; margin-top: 10px; }}
        ul {{ margin-left: 15px; }}
        p {{ margin: 4px 0; }}
    </style>
    </head>
    <body>
    {html_body}
    </body>
    </html>
    """

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as pdf_file:
        pisa_status = pisa.CreatePDF(html_doc, dest=pdf_file)

    if pisa_status.err:
        raise RuntimeError("PDF generation failed due to formatting errors.")
    return {"status": "success", "pdf_path": output_path}

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Convert markdown resume to PDF")
    p.add_argument("--input", default="data/resume.md")
    p.add_argument("--output", default="data/tailored/resume_tailored.pdf")
    args = p.parse_args()

    try:
        res = convert_md_to_pdf(args.input, args.output)
        print(json.dumps(res, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))
        sys.exit(1)