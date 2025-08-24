from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

def generate_pdf_report(report_data: dict, file_path: str):
    """Generates a PDF report from a dictionary of data."""
    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()
    story = []

    for key, value in report_data.items():
        story.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b>", styles['h2']))
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    for sub_key, sub_value in item.items():
                        story.append(Paragraph(f"<b>{sub_key.replace('_', ' ').title()}:</b> {sub_value}", styles['Normal']))
                    story.append(Spacer(1, 0.2 * inch))
                else:
                    story.append(Paragraph(str(item), styles['Normal']))
        else:
            story.append(Paragraph(str(value), styles['Normal']))
        story.append(Spacer(1, 0.2 * inch))

    doc.build(story)
