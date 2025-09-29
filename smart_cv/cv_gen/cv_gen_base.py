"""Resume/CV PDF generation module with flexible section-based architecture."""

import re
import os
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional, Union, Callable
from pathlib import Path
from functools import wraps

from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    ListFlowable,
    ListItem,
    PageBreak,
    Flowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER


# Sentinel object for page breaks
PAGE_BREAK = object()


@dataclass
class Section:
    """
    Represents a section of a resume.

    Examples:
        >>> s = Section(content="Hello world", header="INTRO")
        >>> s.id
        'intro'
        >>> s2 = Section.from_dict({'content': 'Test', 'header': 'About'})
        >>> s2.header
        'About'
    """

    content: Union[str, list[str], list[Flowable], Any]
    header: Optional[str] = None
    id: Optional[str] = None
    kind: Optional[str] = None
    style: Optional[dict] = None

    def __post_init__(self):
        if self.id is None and self.header:
            # Generate ID from header
            self.id = re.sub(r'[^a-z0-9_]', '_', self.header.lower()).strip('_')
        elif self.id is None:
            # Generate unique ID
            import uuid

            self.id = f"section_{uuid.uuid4().hex[:8]}"

    @classmethod
    def from_dict(cls, d: dict) -> 'Section':
        """Create a Section from a dictionary."""
        return cls(**d)


def _colorize_links(text: str, *, color: str = '#2056a5') -> str:
    """
    Add color to all <a> links in text.

    >>> _colorize_links('<a href="#">test</a>')
    "<a href='#'><font color='#2056a5'>test</font></a>"
    """

    def _replace_link(match):
        tag, inner = match.group(1), match.group(2)
        if '<font' in inner:
            return f"<a{tag}>{inner}</a>"
        return f"<a{tag}><font color='{color}'>{inner}</font></a>"

    return re.sub(r"<a([^>]*)>(.*?)</a>", _replace_link, text, flags=re.DOTALL)


def _make_colored_paragraph(
    text: str, style, *, link_color: str = '#2056a5'
) -> Paragraph:
    """Create a Paragraph with colored links."""
    return Paragraph(_colorize_links(text, color=link_color), style)


def _make_styles(
    *,
    title_size: int = 24,
    header_size: int = 12,
    subheader_size: int = 11,
    body_size: int = 10,
    header_color: str = "#003366",
    link_color: str = '#2056a5',
) -> dict:
    """Create and return a dictionary of styles for the resume."""
    styles = getSampleStyleSheet()

    custom_styles = {
        'CenterTitle': ParagraphStyle(
            name='CenterTitle',
            fontSize=title_size,
            leading=20,
            alignment=TA_CENTER,
            spaceAfter=10,
            spaceBefore=10,
            bold=True,
        ),
        'Header': ParagraphStyle(
            name='Header',
            fontSize=header_size,
            leading=14,
            spaceBefore=12,
            spaceAfter=6,
            textColor=header_color,
            bold=True,
        ),
        'SubHeader': ParagraphStyle(
            name='SubHeader',
            fontSize=subheader_size,
            leading=13,
            spaceBefore=8,
            spaceAfter=4,
            bold=True,
        ),
        'Body': ParagraphStyle(name='Body', fontSize=body_size, leading=12),
        'BodyWithLinks': ParagraphStyle(
            name='BodyWithLinks', fontSize=body_size, leading=12, underlineProportion=0
        ),
    }

    for name, style in custom_styles.items():
        styles.add(style)

    return styles


def _render_section_content(
    content: Any, styles: dict, *, link_color: str = '#2056a5'
) -> list[Flowable]:
    """
    Convert section content to reportlab Flowables.

    Returns a list of Flowable objects ready to be added to the story.
    """
    flowables = []

    if content == PAGE_BREAK:
        flowables.append(PageBreak())
    elif isinstance(content, str):
        # Check if content has links
        if '<a href=' in content or '<a ' in content:
            flowables.append(
                _make_colored_paragraph(
                    content, styles['BodyWithLinks'], link_color=link_color
                )
            )
        else:
            flowables.append(Paragraph(content, styles['Body']))
    elif isinstance(content, list):
        if all(isinstance(item, Flowable) for item in content):
            # Already flowables
            flowables.extend(content)
        else:
            # List of strings - convert to list items
            items = []
            for item in content:
                if isinstance(item, str):
                    if '<a href=' in item or '<a ' in item:
                        p = _make_colored_paragraph(
                            item, styles['BodyWithLinks'], link_color=link_color
                        )
                    else:
                        p = Paragraph(item, styles['Body'])
                    items.append(ListItem(p, leftIndent=12))

            if items:
                flowables.append(
                    ListFlowable(items, bulletType='bullet', start='•', leftIndent=18)
                )
    elif isinstance(content, Flowable):
        flowables.append(content)

    return flowables


def _section_to_flowables(
    section: Section,
    styles: dict,
    *,
    link_color: str = '#2056a5',
    section_spacing: int = 10,
) -> list[Flowable]:
    """Convert a Section to a list of reportlab Flowables."""
    flowables = []

    # Add header if present
    if section.header:
        header_style = styles.get(
            section.style.get('header_style', 'Header') if section.style else 'Header'
        )
        flowables.append(Paragraph(section.header, header_style))

    # Process content
    content_flowables = _render_section_content(
        section.content, styles, link_color=link_color
    )
    flowables.extend(content_flowables)

    # Add spacing after section
    spacing = (
        section.style.get('spacing_after', section_spacing)
        if section.style
        else section_spacing
    )
    if spacing > 0:
        flowables.append(Spacer(1, spacing))

    return flowables


def mk_experience_section(
    experiences: list[tuple[str, str, list[str]]],
    *,
    header: str = "EXPERIENCE",
    link_color: str = '#2056a5',
    item_spacing: int = 4,
) -> Section:
    """
    Create an experience section from a list of experience tuples.

    Args:
        experiences: List of (title, dates, bullet_points) tuples
        header: Section header
        link_color: Color for links

    >>> exp = [("Company - Role", "2020-2023", ["Did stuff", "Made things"])]
    >>> section = mk_experience_section(exp)
    >>> section.header
    'EXPERIENCE'
    """
    styles = _make_styles(link_color=link_color)
    flowables = []

    from .cv_gen_base import PAGE_BREAK  # Ensure PAGE_BREAK is in scope if needed

    for item in experiences:
        if item is PAGE_BREAK:
            flowables.append(PageBreak())
            continue
        title, dates, bullets = item
        # Add subheader
        flowables.append(
            Paragraph(f"<b>{title}</b> | <i>{dates}</i>", styles['SubHeader'])
        )

        # Add bullet points
        items = []
        for bullet in bullets:
            if '<a href=' in bullet or '<a ' in bullet:
                p = _make_colored_paragraph(
                    bullet, styles['BodyWithLinks'], link_color=link_color
                )
            else:
                p = Paragraph(bullet, styles['Body'])
            items.append(ListItem(p, leftIndent=12))

        if items:
            flowables.append(
                ListFlowable(items, bulletType='bullet', start='•', leftIndent=18)
            )
    flowables.append(Spacer(1, item_spacing))

    return Section(content=flowables, header=header, kind="experience")


def mk_list_section(
    items: list[str], *, header: str, link_color: str = '#2056a5'
) -> Section:
    """
    Create a section with a bulleted list.

    >>> section = mk_list_section(["Item 1", "Item 2"], header="SKILLS")
    >>> section.header
    'SKILLS'
    """
    return Section(content=items, header=header, kind="list")


def mk_header_section(
    name: str, contact_lines: list[str], *, link_color: str = '#2056a5'
) -> list[Section]:
    """
    Create header sections (name and contact info).

    Returns two sections: one for the name, one for contact info.
    """
    name_section = Section(
        content=f"<b>{name}</b>",
        id="name",
        kind="title",
        style={'header_style': 'CenterTitle', 'spacing_after': 0},
    )

    contact_sections = []
    for line in contact_lines:
        contact_sections.append(
            Section(
                content=line,
                id=f"contact_{len(contact_sections)}",
                kind="contact",
                style={'spacing_after': 0},
            )
        )

    return [name_section] + contact_sections


def mk_resume(
    sections: Iterable[Union[Section, Any]],
    *,
    pdf_path: str = "resume.pdf",
    page_size=letter,
    margins: dict = None,
    link_color: str = '#2056a5',
    page_breaks_before: list[str] = None,
    style_overrides: dict = None,
    section_spacing: int = 12,
    experience_item_spacing: int = 6,
) -> str:
    """
    Generate a resume PDF from sections.

    Args:
        sections: Iterable of Section objects or PAGE_BREAK sentinel
        pdf_path: Path where PDF will be saved
        page_size: Page size (default: letter)
        margins: Dict with keys 'right', 'left', 'top', 'bottom'
        link_color: Color for hyperlinks
        page_breaks_before: List of section IDs to insert page breaks before
        style_overrides: Dict of style customizations

    Returns:
        Path to the generated PDF

    >>> sections = [Section(content="Test", header="TEST")]
    >>> path = mk_resume(sections, pdf_path="/tmp/test.pdf")
    >>> Path(path).exists()
    True
    """
    # Default margins
    if margins is None:
        margins = {'right': 50, 'left': 50, 'top': 50, 'bottom': 50}

    pdf_path = os.path.expanduser(pdf_path)

    # Create document
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=page_size,
        rightMargin=margins.get('right', 50),
        leftMargin=margins.get('left', 50),
        topMargin=margins.get('top', 50),
        bottomMargin=margins.get('bottom', 50),
    )

    # Get styles
    styles = _make_styles(link_color=link_color)

    # Apply style overrides if provided
    if style_overrides:
        for style_name, overrides in style_overrides.items():
            if style_name in styles:
                for attr, value in overrides.items():
                    setattr(styles[style_name], attr, value)

    # Build story
    story = []
    page_breaks_before = page_breaks_before or []

    for item in sections:
        if item == PAGE_BREAK:
            story.append(PageBreak())
        elif isinstance(item, Section):
            # Check if we need a page break before this section
            if item.id in page_breaks_before:
                story.append(PageBreak())

            # Use custom spacing for experience section
            if item.kind == "experience":
                # Rebuild the section with custom item spacing
                rebuilt_section = mk_experience_section(
                    item.content,
                    header=item.header,
                    link_color=link_color,
                    item_spacing=experience_item_spacing,
                )
                flowables = _section_to_flowables(
                    rebuilt_section,
                    styles,
                    link_color=link_color,
                    section_spacing=section_spacing,
                )
            else:
                flowables = _section_to_flowables(
                    item, styles, link_color=link_color, section_spacing=section_spacing
                )
            story.extend(flowables)

    # Build PDF
    doc.build(story)

    return pdf_path
