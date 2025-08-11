from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors
from io import BytesIO


def _add_page_number(canvas_obj, doc):
    page_num_text = f"Page {doc.page}"
    width, height = letter
    canvas_obj.setFont('Helvetica', 9)
    canvas_obj.drawCentredString(width / 2.0, 20, page_num_text)


def _boxed_section(elements_list, table_style=None):
    """
    Helper function to wrap a list of flowables in a single cell table with border.
    """
    if not table_style:
        table_style = TableStyle([
            ('BOX', (0, 0), (-1, -1), 3, colors.black),  # thicker black border, width 3
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ])
    tbl = Table([[elements_list]], colWidths=[450])
    tbl.setStyle(table_style)
    return tbl



def create_mom_pdf(mom_data_dict):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            topMargin=50, leftMargin=60, rightMargin=60, bottomMargin=50)
    styles = getSampleStyleSheet()

    # Styles for July style (custom)
    title_style = ParagraphStyle(
        'TitleStyle', parent=styles['Title'], fontSize=18, leading=22, alignment=TA_CENTER,
        spaceAfter=12, textColor=colors.black
    )
    metadata_style = ParagraphStyle(
        'Meta', parent=styles['Normal'], fontSize=12, leading=16, alignment=TA_LEFT, spaceAfter=6
    )
    section_title_style = ParagraphStyle(
        'SectionTitle', parent=styles['Heading2'], fontSize=14, leading=18,
        spaceAfter=6, textColor=colors.black
    )
    normal_style = ParagraphStyle(
        'Normal', parent=styles['Normal'], fontSize=12, leading=16, spaceAfter=6
    )
    bullet_style = ParagraphStyle(
        'Bullet', parent=styles['Normal'], fontSize=12, leading=16, leftIndent=15, bulletIndent=5
    )

    elements = []

    # Title
    if mom_data_dict.get('title'):
        elements.append(Paragraph(f"<b>{mom_data_dict['title']}</b>", title_style))
        elements.append(Spacer(1, 6))

    # Date / Time / Location
    date_line = []
    if mom_data_dict.get('date'):
        date_line.append(f"<b>Date:</b> {mom_data_dict['date']}")
    if mom_data_dict.get('time'):
        date_line.append(f"<b>Time:</b> {mom_data_dict['time']}")
    if mom_data_dict.get('location'):
        date_line.append(f"<b>Location:</b> {mom_data_dict['location']}")
    for item in date_line:
        elements.append(Paragraph(item, metadata_style))
    elements.append(Spacer(1, 10))

    # Attendees
    if mom_data_dict.get('attendees'):
        content = [Paragraph("<b>Attendees:</b>", section_title_style)]
        if isinstance(mom_data_dict['attendees'], list):
            for idx, name in enumerate(mom_data_dict['attendees'], start=1):
                content.append(Paragraph(f"{idx}. {name}", normal_style))
        else:
            content.append(Paragraph(str(mom_data_dict['attendees']), normal_style))
        content.append(Spacer(1, 10))
        elements.append(_boxed_section(content))

    # Agenda
    if mom_data_dict.get('agenda'):
        content = [Paragraph("<b>Agenda:</b>", section_title_style)]
        agenda_items = mom_data_dict['agenda']
        if isinstance(agenda_items, list):
            for item in agenda_items:
                content.append(Paragraph(f"• {item}", bullet_style))
        else:
            for line in agenda_items.split('\n'):
                content.append(Paragraph(f"• {line.strip()}", bullet_style))
        content.append(Spacer(1, 10))
        elements.append(_boxed_section(content))

    # Discussions (NO BOX)
    if mom_data_dict.get('discussions'):
        content = [Paragraph("<b>Points of Discussion:</b>", section_title_style)]
        discussions = mom_data_dict['discussions']
        if isinstance(discussions, list):
            for idx, section in enumerate(discussions, start=1):
                title = section.get('title', f"Section {idx}")
                content.append(Paragraph(f"<b>{idx}. {title}</b>", normal_style))
                points = section.get('points', [])
                for point in points:
                    if isinstance(point, dict):
                        text = point.get('text')
                        if text:
                            content.append(Paragraph(f"• {text}", bullet_style))
                        subpoints = point.get('subpoints', [])
                        for sp in subpoints:
                            content.append(Paragraph(f"– {sp}", bullet_style))
                    else:
                        content.append(Paragraph(f"• {point}", bullet_style))
                content.append(Spacer(1, 6))
        else:
            content.append(Paragraph(str(discussions), normal_style))
        content.append(Spacer(1, 10))

        # Append discussions directly without boxing
        elements.extend(content)

    # Actions
    if mom_data_dict.get('actions'):
        content = [Paragraph("<b>Action Plans:</b>", section_title_style)]
        actions = mom_data_dict['actions']
        if isinstance(actions, list):
            for item in actions:
                content.append(Paragraph(f"• {item}", bullet_style))
        else:
            for line in actions.split('\n'):
                content.append(Paragraph(f"• {line.strip()}", bullet_style))
        content.append(Spacer(1, 10))
        elements.append(_boxed_section(content))

    # Conclusion
    if mom_data_dict.get('conclusion'):
        content = [Paragraph("<b>Conclusion:</b>", section_title_style)]
        conclusion = mom_data_dict['conclusion']
        if isinstance(conclusion, str):
            for para in conclusion.split('\n\n'):
                content.append(Paragraph(para.strip(), normal_style))
        else:
            content.append(Paragraph(str(conclusion), normal_style))
        content.append(Spacer(1, 10))
        elements.append(_boxed_section(content))

    # Summary
    if mom_data_dict.get('summary'):
        content = [Paragraph("<b>Summary:</b>", section_title_style)]
        summary = mom_data_dict['summary']
        if isinstance(summary, str):
            for para in summary.split('\n\n'):
                content.append(Paragraph(para.strip(), normal_style))
        else:
            content.append(Paragraph(str(summary), normal_style))
        elements.append(_boxed_section(content))

    doc.build(elements, onFirstPage=_add_page_number, onLaterPages=_add_page_number)
    buffer.seek(0)
    return buffer
