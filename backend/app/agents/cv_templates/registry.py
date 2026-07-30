"""15 CV template configs + generate_cv_docx entry point."""

from typing import Optional

from app.schemas.tailored import TailoredResume

from .base import CVDocxRenderer, TemplateConfig

# ── 15 Template Definitions ──────────────────────────────────────────

TEMPLATE_REGISTRY: dict[str, TemplateConfig] = {
    "ats_classic": TemplateConfig(
        id="ats_classic",
        name="ATS Classic",
        font_name="Calibri",
        header_bg=None,
        heading_color=(0, 0, 0),
        heading_style="rule",
        name_size=16.0,          # CSS 22px → 16pt
        name_align="center",
        contact_align="center",
        header_rule_color=(0, 0, 0),
        header_rule_sz=16,
    ),
    "microsoft_modern": TemplateConfig(
        id="microsoft_modern",
        name="Microsoft Modern",
        font_name="Calibri",
        header_bg=(43, 87, 154),
        header_text_color=(255, 255, 255),
        designation_color=(201, 217, 240),
        heading_color=(43, 87, 154),
        heading_style="color_rule",
        name_size=18.0,          # CSS 24px → 18pt
        name_align="left",
        contact_align="left",
    ),
    "corporate_blue": TemplateConfig(
        id="corporate_blue",
        name="Corporate Blue",
        font_name="Calibri",
        header_bg=None,
        heading_color=(26, 58, 92),
        heading_style="rule",
        rule_color=(26, 58, 92),
        name_size=16.0,          # CSS 22px → 16pt
        name_align="center",
        designation_color=(26, 58, 92),
        contact_align="center",
    ),
    "executive_dark": TemplateConfig(
        id="executive_dark",
        name="Executive Dark",
        font_name="Calibri",
        header_bg=None,
        heading_color=(26, 26, 46),
        heading_style="left_border",
        rule_color=(99, 102, 241),
        name_size=11.0,          # CSS 15px sidebar → 11pt
        name_align="left",
        contact_align="left",
        two_column=(0.28, (26, 26, 46)),
    ),
    "clean_minimal": TemplateConfig(
        id="clean_minimal",
        name="Clean Minimal",
        font_name="Calibri",
        header_bg=None,
        heading_color=(100, 100, 100),
        heading_style="rule",
        rule_color=(200, 200, 200),
        name_size=20.0,          # CSS 26px → 20pt
        name_align="left",
        designation_color=(140, 140, 140),
        contact_align="left",
        heading_uppercase=True,
    ),
    "charcoal_gold": TemplateConfig(
        id="charcoal_gold",
        name="Charcoal Gold",
        font_name="Calibri",
        header_bg=(30, 42, 58),
        header_text_color=(255, 255, 255),
        designation_color=(201, 168, 76),
        heading_color=(30, 42, 58),
        heading_style="left_border",
        rule_color=(201, 168, 76),
        name_size=16.0,          # CSS 22px → 16pt
        name_align="left",
        contact_align="left",
    ),
    "elegant_serif": TemplateConfig(
        id="elegant_serif",
        name="Elegant Serif",
        font_name="Georgia",
        header_bg=None,
        heading_color=(44, 24, 16),
        heading_style="rule",
        rule_color=(196, 168, 138),
        name_size=16.0,          # CSS 22px → 16pt
        name_align="center",
        designation_color=(122, 92, 71),
        contact_align="center",
        serif_font=True,
    ),
    "tech_pro": TemplateConfig(
        id="tech_pro",
        name="Tech Pro",
        font_name="Courier New",
        header_bg=(13, 17, 23),
        header_text_color=(230, 237, 243),
        designation_color=(88, 166, 255),
        heading_color=(121, 192, 255),
        heading_style="rule",
        name_size=15.0,          # CSS 20px → 15pt
        name_align="left",
        contact_align="left",
    ),
    "creative_teal": TemplateConfig(
        id="creative_teal",
        name="Creative Teal",
        font_name="Calibri",
        header_bg=(13, 148, 136),
        header_text_color=(255, 255, 255),
        designation_color=(204, 251, 241),
        heading_color=(13, 148, 136),
        heading_style="color_rule",
        name_size=16.0,          # CSS 22px → 16pt
        name_align="left",
        contact_align="left",
    ),
    "linkedin_style": TemplateConfig(
        id="linkedin_style",
        name="LinkedIn Style",
        font_name="Calibri",
        header_bg=None,
        heading_color=(0, 119, 181),
        heading_style="rule",
        rule_color=(180, 180, 180),
        name_size=15.0,          # CSS 20px → 15pt
        name_align="left",
        designation_color=(0, 119, 181),
        contact_align="left",
        header_rule_color=(0, 119, 181),
        header_rule_sz=24,
    ),
    "harvard_classic": TemplateConfig(
        id="harvard_classic",
        name="Harvard Classic",
        font_name="Times New Roman",
        header_bg=None,
        heading_color=(165, 28, 48),
        heading_style="rule",
        rule_color=(165, 28, 48),
        name_size=16.0,          # CSS 22px → 16pt
        name_align="center",
        contact_align="center",
        serif_font=True,
        header_rule_color=(0, 0, 0),
        header_rule_sz=12,
    ),
    "compact_dense": TemplateConfig(
        id="compact_dense",
        name="Compact Dense",
        font_name="Arial",
        header_bg=None,
        heading_color=(51, 65, 85),
        heading_style="shaded_box",
        name_size=12.0,          # CSS 16px → 12pt
        name_align="left",
        contact_align="left",
    ),
    "two_column_split": TemplateConfig(
        id="two_column_split",
        name="Two Column Split",
        font_name="Calibri",
        header_bg=None,
        heading_color=(30, 58, 95),
        heading_style="color_rule",
        name_size=12.0,          # CSS 16px → 12pt
        name_align="left",
        contact_align="left",
        two_column=(0.30, (30, 58, 95)),
    ),
    "green_professional": TemplateConfig(
        id="green_professional",
        name="Green Professional",
        font_name="Calibri",
        header_bg=None,
        heading_color=(20, 83, 45),
        heading_style="left_border",
        rule_color=(22, 163, 74),
        name_size=16.0,          # CSS 22px → 16pt
        name_align="left",
        designation_color=(21, 128, 61),
        contact_align="left",
    ),
    "purple_modern": TemplateConfig(
        id="purple_modern",
        name="Purple Modern",
        font_name="Calibri",
        header_bg=(76, 29, 149),
        header_text_color=(255, 255, 255),
        designation_color=(233, 213, 255),
        heading_color=(109, 40, 217),
        heading_style="left_border",
        rule_color=(168, 85, 247),
        name_size=16.0,          # CSS 22px → 16pt
        name_align="left",
        contact_align="left",
    ),
}

TEMPLATE_LIST = [
    {"id": cfg.id, "name": cfg.name}
    for cfg in TEMPLATE_REGISTRY.values()
]


def generate_cv_docx(
    tailored: TailoredResume,
    template_id: str,
    candidate_name: str,
    contact_info: Optional[dict] = None,
) -> bytes:
    """Generate a DOCX for the given tailored resume in the requested template.

    Args:
        tailored: The tailored resume data from the pipeline.
        template_id: One of the 15 template IDs (e.g. "microsoft_modern").
        candidate_name: Full name to display on the CV.
        contact_info: Dict with keys: location, email, phone, linkedin, designation.

    Returns:
        DOCX bytes ready for streaming to the client.

    Raises:
        ValueError: If template_id is not in TEMPLATE_REGISTRY.
    """
    if template_id not in TEMPLATE_REGISTRY:
        raise ValueError(f"Unknown template: {template_id!r}. Valid IDs: {list(TEMPLATE_REGISTRY)}")
    config = TEMPLATE_REGISTRY[template_id]
    renderer = CVDocxRenderer(config)
    return renderer.render(tailored, candidate_name, contact_info)
