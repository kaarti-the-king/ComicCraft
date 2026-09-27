import os
import re
from datetime import datetime
from fpdf import FPDF


class ComicPDF(FPDF):
    """Custom FPDF layout with page numbering and header styling."""

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, "ComicCraft AI Story Production", ln=True, align="R")
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(160, 160, 160)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def clean_latin_text(text: str) -> str:
    """Sanitizes unicode quotation marks, dashes, and unsupported characters for core PDF fonts."""
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2014": "-",
        "\u2013": "-",
        "\u2026": "...",
        "\u00a0": " ",
    }
    for orig, rep in replacements.items():
        text = text.replace(orig, rep)
    # Remove emojis or characters outside standard latin-1 range
    return re.sub(r"[^\x00-\xFF]", "", text)


def save_pdf(layout: list) -> str:
    """
    Compiles the full comic layout into a multi-page PDF document.
    Each panel is rendered on an individual page.
    Returns the relative path to the generated PDF file.
    """
    export_folder = os.path.join("static", "exports")
    os.makedirs(export_folder, exist_ok=True)

    pdf = ComicPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)

    font_path = os.path.join("static", "fonts", "DejaVuSans.ttf")
    has_unicode_font = os.path.exists(font_path)

    if has_unicode_font:
        pdf.add_font("DejaVu", "", font_path, uni=True)
        main_font = "DejaVu"
    else:
        main_font = "Helvetica"

    for panel in layout:
        pdf.add_page()

        panel_num = panel.get("panel", 1)
        panel_title = clean_latin_text(panel.get("title", f"Panel {panel_num}"))
        image_path = panel.get("image_path", "")
        story_text = clean_latin_text(panel.get("text", ""))
        scene_desc = clean_latin_text(panel.get("scene_description", ""))

        # Panel Title
        pdf.set_font(main_font, "B" if not has_unicode_font else "", 16)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 10, f"Panel {panel_num}: {panel_title}", ln=True, align="C")
        pdf.ln(3)

        # Image placement
        image_width = 110
        x_centered = (pdf.w - image_width) / 2
        y_image = pdf.get_y()

        if os.path.exists(image_path):
            pdf.image(image_path, x=x_centered, y=y_image, w=image_width, h=image_width)
            pdf.set_y(y_image + image_width + 8)
        else:
            pdf.set_font(main_font, "I" if not has_unicode_font else "", 11)
            pdf.set_text_color(220, 38, 38)
            pdf.cell(0, 10, f"[Image Missing: {image_path}]", ln=True, align="C")
            pdf.ln(5)

        # Scene context
        if scene_desc:
            pdf.set_font(main_font, "I" if not has_unicode_font else "", 10)
            pdf.set_text_color(100, 116, 139)
            pdf.multi_cell(0, 6, scene_desc, align="C")
            pdf.ln(4)

        # Narrative Body
        pdf.set_font(main_font, "" if not has_unicode_font else "", 11)
        pdf.set_text_color(51, 65, 85)

        story_lines = story_text.splitlines()
        if story_lines and story_lines[0].strip().lower().startswith("**panel"):
            story_lines = story_lines[1:]

        cleaned_text = "\n".join(story_lines).strip()
        pdf.multi_cell(0, 7, cleaned_text, align="L")

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"comic_{timestamp}.pdf"
    pdf_output_path = os.path.join(export_folder, filename)
    pdf.output(pdf_output_path)

    return pdf_output_path