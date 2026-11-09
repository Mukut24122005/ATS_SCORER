import io
import logging
from html.parser import HTMLParser
from xml.sax.saxutils import escape

try:
    from weasyprint import HTML
    WEASYPRINT_INSTALLED = True
except (ImportError, OSError) as exc:
    logger = logging.getLogger('ats_resume_scorer')
    logger.warning('WeasyPrint unavailable; using ReportLab PDF fallback: %s', exc)
    WEASYPRINT_INSTALLED = False

logger = logging.getLogger('ats_resume_scorer')


class _ReportTextParser(HTMLParser):
    _BLOCK_TAGS = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'tr'}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.paragraphs: list[tuple[str, str]] = []
        self._tag = 'p'
        self._parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {'script', 'style'}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag in self._BLOCK_TAGS or tag == 'br':
            self._flush()
            self._tag = tag if tag in self._BLOCK_TAGS else 'p'
            if tag == 'li':
                self._parts.append('- ')
        elif tag in {'td', 'th'} and self._parts:
            self._parts.append(' | ')

    def handle_endtag(self, tag: str) -> None:
        if tag in {'script', 'style'} and self._skip_depth:
            self._skip_depth -= 1
            return
        if not self._skip_depth and tag in self._BLOCK_TAGS:
            self._flush()

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            text = ' '.join(data.split())
            if text:
                self._parts.append(text)

    def _flush(self) -> None:
        text = ' '.join(part for part in self._parts if part).strip()
        if text:
            self.paragraphs.append((self._tag, text))
        self._parts.clear()
        self._tag = 'p'


def _generate_reportlab_pdf(html_docs: dict[str, str]) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

    output = io.BytesIO()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='ReportSection',
        parent=styles['Title'],
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=18,
    ))
    styles.add(ParagraphStyle(
        name='ReportSubheading',
        parent=styles['Heading2'],
        textColor=colors.HexColor('#1e40af'),
        spaceBefore=8,
        spaceAfter=5,
    ))
    body_style = styles['BodyText']
    body_style.leading = 14
    body_style.spaceAfter = 7

    document = SimpleDocTemplate(
        output,
        pagesize=letter,
        rightMargin=0.7 * inch,
        leftMargin=0.7 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title='ATS Resume Analysis Report',
    )
    story = []
    for index, (name, html_doc) in enumerate(html_docs.items()):
        if index:
            story.append(PageBreak())
        story.append(Paragraph(escape(name.replace('_', ' ').title()), styles['ReportSection']))
        parser = _ReportTextParser()
        parser.feed(html_doc)
        parser.close()
        parser._flush()
        for tag, text in parser.paragraphs:
            style = styles['ReportSubheading'] if tag.startswith('h') else body_style
            story.append(Paragraph(escape(text), style))
            story.append(Spacer(1, 3))

    if not story:
        story.append(Paragraph('No report content available.', body_style))
    document.build(story)
    return output.getvalue()


def generate_combined_pdf(html_docs: dict[str, str]) -> bytes:
    if not WEASYPRINT_INSTALLED:
        return _generate_reportlab_pdf(html_docs)
        
    documents = []
    
    # Render all 3 HTML strings to WeasyPrint Document objects
    for name, html_str in html_docs.items():
        doc = HTML(string=html_str).render()
        documents.append(doc)
    
    # Merge them into the first document
    first_doc = documents[0]
    for other_doc in documents[1:]:
        for page in other_doc.pages:
            first_doc.pages.append(page)
            
    # Write combined PDF bytes
    pdf_bytes = first_doc.write_pdf()
    return pdf_bytes