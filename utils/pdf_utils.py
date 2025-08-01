from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from io import BytesIO


def _add_page_number(canvas_obj, doc):
    """
    Draw page number at bottom center of the page.
    """
    page_num_text = f"Page {doc.page}"
    canvas_obj.saveState()
    canvas_obj.setFont('Helvetica', 9)
    width, height = letter
    canvas_obj.drawCentredString(width / 2.0, 20, page_num_text)
    canvas_obj.restoreState()


def create_boxed_section(title, content_elements, width=480):
    """
    Create a table with a border around content elements.

    :param title: Section title Paragraph (already styled)
    :param content_elements: list of Paragraphs or flowables inside the box
    :param width: total width of the boxed section
    :return: Table flowable representing boxed section
    """
    # Wrap content elements into a ListFlowable so they render properly as a group inside table cell
    content_list_flowable = ListFlowable(content_elements, leftIndent=10 if content_elements else 0)

    # Combine the title Paragraph and the content ListFlowable vertically
    content = [title, Spacer(1, 6), content_list_flowable]

    # Wrap content list in a Table cell (one cell, one column)
    data = [[content]]

    table = Table(data, colWidths=[width])

    tbl_style = TableStyle([
        ('BOX', (0, 0), (-1, -1), 1.2, colors.HexColor('#203864')),  # Dark blue border
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dbe9f7')),  # Light blue background for title
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ])

    table.setStyle(tbl_style)
    return table


def create_mom_pdf(mom_data_dict):
    """
    Generates a styled PDF Minutes of Meeting with font adjustments and boxed sections.

    Parameters:
        mom_data_dict (dict): Dictionary with keys:
            - title (str)
            - date (str)
            - time (str)
            - attendees (list or str)
            - agenda (list or str)
            - discussions (str or list of sections)
            - actions (list or str)
            - conclusion (str)
            - summary (str)

    Returns:
        BytesIO: In-memory PDF file buffer ready to be written or attached to email.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            topMargin=50, leftMargin=60, rightMargin=60, bottomMargin=50)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        name='TitleStyle',
        parent=styles['Title'],
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#0A3D62'),
        spaceAfter=16,
    )

    section_title_style = ParagraphStyle(
        name='SectionTitleStyle',
        parent=styles['Heading2'],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#1E3799'),
        spaceAfter=12,
        leftIndent=0,
        fontName='Helvetica-Bold'
    )

    normal_style = ParagraphStyle(
        name='NormalText',
        parent=styles['Normal'],
        fontSize=12,
        leading=16,
        textColor=colors.black,
        spaceAfter=6,
        leftIndent=0,
    )

    bullet_style = ParagraphStyle(
        name='BulletText',
        parent=normal_style,
        leftIndent=20,
        bulletIndent=10,
        fontSize=12,
        leading=16,
        textColor=colors.black,
    )

    subbullet_style = ParagraphStyle(
        name='SubBulletText',
        parent=normal_style,
        leftIndent=40,
        bulletIndent=30,
        fontSize=12,
        leading=16,
        textColor=colors.black,
    )

    elements = []

    # Title (Centered with color)
    title = mom_data_dict.get('title')
    if title:
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 12))

    # Date and Time combined as one paragraph for neatness
    date = mom_data_dict.get('date')
    time = mom_data_dict.get('time')
    if date or time:
        dt_text = ""
        if date:
            dt_text += f"<b>Date:</b> {date} "
        if time:
            dt_text += f"<b>Time:</b> {time}"
        elements.append(Paragraph(dt_text.strip(), normal_style))
        elements.append(Spacer(1, 10))

    # Attendees section boxed
    attendees = mom_data_dict.get('attendees')
    if attendees:
        if isinstance(attendees, list):
            attendees_str = ', '.join(attendees)
        else:
            attendees_str = str(attendees)
        attend_title = Paragraph("Attendees:", section_title_style)
        attend_paragraph = Paragraph(attendees_str, normal_style)
        elements.append(create_boxed_section(attend_title, [attend_paragraph]))
        elements.append(Spacer(1, 12))

    # Helper to build bullet list paragraphs
    def build_bullet_paragraphs(items):
        paras = []
        if isinstance(items, list):
            for item in items:
                if item:
                    paras.append(Paragraph(f"• {item}", bullet_style))
        elif isinstance(items, str):
            lines = [line.strip() for line in items.split('\n') if line.strip()]
            for line in lines:
                paras.append(Paragraph(f"• {line}", bullet_style))
        return paras

    # Helper to build structured discussion flowables
    def build_discussion_flowables(discussions):
        flowables = []
        if isinstance(discussions, list):
            for idx, section in enumerate(discussions, start=1):
                sec_title = section.get('title', f"Section {idx}")
                flowables.append(Paragraph(f"{idx}. {sec_title}:", section_title_style))
                points = section.get('points', [])
                for point in points:
                    if isinstance(point, dict):
                        text = point.get('text', '')
                        if text:
                            flowables.append(Paragraph(f"• {text}", bullet_style))
                        subpoints = point.get('subpoints', [])
                        for sp in subpoints:
                            flowables.append(Paragraph(f"– {sp}", subbullet_style))
                    else:
                        flowables.append(Paragraph(f"• {point}", bullet_style))
                flowables.append(Spacer(1, 8))
        elif isinstance(discussions, str):
            paras = [p.strip() for p in discussions.strip().split('\n\n') if p.strip()]
            for para in paras:
                flowables.append(Paragraph(para, normal_style))
                flowables.append(Spacer(1, 6))
        else:
            flowables.append(Paragraph(str(discussions), normal_style))
        return flowables

    # Agenda section boxed
    agenda = mom_data_dict.get('agenda')
    if agenda:
        agenda_title = Paragraph("Agenda:", section_title_style)
        agenda_content = build_bullet_paragraphs(agenda)
        elements.append(create_boxed_section(agenda_title, agenda_content))
        elements.append(Spacer(1, 12))

    # Key Discussions section: Box only the title, content flows normally with page breaks
    discussions = mom_data_dict.get('discussions')
    if discussions:
        # Boxed title only
        discussion_title = Paragraph("Key Discussions:", section_title_style)
        elements.append(create_boxed_section(discussion_title, []))  # Box title only with no content
        elements.append(Spacer(1, 6))

        # Add discussion content flowables after box
        discussion_flowables = build_discussion_flowables(discussions)
        elements.extend(discussion_flowables)
        elements.append(Spacer(1, 12))

    # Action Points / Decisions boxed
    actions = mom_data_dict.get('actions')
    if actions:
        actions_title = Paragraph("Action Points / Decisions:", section_title_style)
        actions_content = build_bullet_paragraphs(actions)
        elements.append(create_boxed_section(actions_title, actions_content))
        elements.append(Spacer(1, 12))

    # Conclusion section boxed
    conclusion = mom_data_dict.get('conclusion')
    if conclusion:
        conclusion_title = Paragraph("Conclusion:", section_title_style)
        if isinstance(conclusion, str):
            conclusion_paras_text = [p.strip() for p in conclusion.strip().split('\n\n') if p.strip()]
            conclusion_paras = [Paragraph(p, normal_style) for p in conclusion_paras_text]
        else:
            conclusion_paras = [Paragraph(str(conclusion), normal_style)]
        elements.append(create_boxed_section(conclusion_title, conclusion_paras))
        elements.append(Spacer(1, 12))

    # Summary (optional) boxed
    summary = mom_data_dict.get('summary')
    if summary:
        summary_title = Paragraph("Summary:", section_title_style)
        if isinstance(summary, str):
            summary_paras_text = [p.strip() for p in summary.strip().split('\n\n') if p.strip()]
            summary_paras = [Paragraph(p, normal_style) for p in summary_paras_text]
        else:
            summary_paras = [Paragraph(str(summary), normal_style)]
        elements.append(create_boxed_section(summary_title, summary_paras))
        elements.append(Spacer(1, 12))

    # Build the PDF with page numbers
    doc.build(elements, onFirstPage=_add_page_number, onLaterPages=_add_page_number)

    buffer.seek(0)
    return buffer
