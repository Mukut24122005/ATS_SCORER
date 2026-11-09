from typing import Dict, List

from backend.models.schemas import IssueDetail


def _issue(
    title: str,
    severity: str,
    impact: str,
    explanation: str,
    location: str,
    fix: str,
    actions: List[str],
    example: str,
) -> IssueDetail:
    return IssueDetail(
        issue_title=title,
        severity_level=severity,
        ats_impact=impact,
        explanation=explanation,
        where_it_appears=location,
        how_to_fix=fix,
        action_items=actions,
        example_improvement=example,
    )


def analyze_issues(
    resume_text: str,
    parsed_resume: Dict,
    skills: List[str],
    projects: List[Dict],
    action_verbs: List[str],
    skill_validation: Dict,
    scores: Dict,
    contact_info: Dict,
) -> List[IssueDetail]:
    issues: List[IssueDetail] = []

    formatting_score = scores.get("formatting_score", 0)
    if formatting_score < 14:
        issues.append(_issue(
            "Improve resume structure",
            "high" if formatting_score < 10 else "moderate",
            "Unclear sections and layout can make important information harder for an ATS to identify.",
            "The resume received a low formatting score.",
            "Across the resume, especially section headings and experience entries.",
            "Use clear, conventional section headings and consistent formatting.",
            [
                "Use headings such as Experience, Education, Skills, and Projects.",
                "Keep dates, job titles, and employer names consistently formatted.",
            ],
            "Experience\\nSoftware Engineer | Example Company | 2022–Present",
        ))

    keywords_score = scores.get("keywords_score", 0)
    if keywords_score < 17:
        issues.append(_issue(
            "Strengthen relevant keywords",
            "high" if keywords_score < 12 else "moderate",
            "Relevant skills and terminology help ATS systems match a resume to a role.",
            "The resume received a low keyword score based on the extracted skills and terms.",
            "Skills section and experience or project descriptions.",
            "Include relevant skills in context, using terminology that accurately reflects your experience.",
            [
                "Add role-relevant skills that you genuinely possess.",
                "Describe where and how you used each important skill.",
            ],
            "Built data pipelines with Python and SQL to automate weekly reporting.",
        ))

    content_score = scores.get("content_score", 0)
    if content_score < 17 or len(action_verbs) < 3:
        issues.append(_issue(
            "Make achievements more specific",
            "moderate",
            "Specific, results-oriented statements make experience easier for recruiters and ATS tools to assess.",
            "The resume could communicate the scope or results of its work more clearly.",
            "Experience and project bullet points.",
            "Lead with an action verb and add measurable results where available.",
            [
                "Describe the action you took and the result.",
                "Add truthful numbers, scale, or time saved when you can support them.",
            ],
            "Automated monthly reporting, reducing preparation time by 30%.",
        ))

    validation_score = scores.get("skill_validation_score", 0)
    unvalidated = skill_validation.get("unvalidated_skills", [])
    if validation_score < 9 or unvalidated:
        examples = ", ".join(str(skill) for skill in unvalidated[:5])
        detail = "Some listed skills are not clearly supported by project or experience evidence."
        if examples:
            detail += f" Skills to substantiate include: {examples}."
        issues.append(_issue(
            "Support skills with evidence",
            "moderate",
            "Evidence helps distinguish demonstrated skills from keyword-only skill lists.",
            detail,
            "Skills section compared with project and experience descriptions.",
            "Connect important skills to concrete work, projects, or outcomes.",
            [
                "Add a project or work example for key skills.",
                "Remove skills that you cannot confidently support with experience.",
            ],
            "Used React and TypeScript to build an accessible dashboard for 500 users.",
        ))

    ats_score = scores.get("ats_compatibility_score", 0)
    if ats_score < 10:
        issues.append(_issue(
            "Improve ATS readability",
            "high" if ats_score < 7 else "moderate",
            "Content that is difficult to parse may be missed or placed in the wrong field by an ATS.",
            "The resume received a low ATS compatibility score.",
            "Document layout and contact header.",
            "Prefer a simple, text-based layout and keep contact details in the main document body.",
            [
                "Avoid using tables, text boxes, or images for essential information.",
                "Use a selectable-text PDF or a standard DOCX document.",
            ],
            "Name | Email | Phone\\nExperience\\nCompany — Job Title — Dates",
        ))

    if not contact_info.get("email") and not contact_info.get("phone"):
        issues.append(_issue(
            "Add contact information",
            "high",
            "Recruiters may be unable to contact you if your resume has no detectable email address or phone number.",
            "No email address or phone number was detected in the parsed resume.",
            "Contact header at the top of the resume.",
            "Add at least one professional way to contact you as plain text.",
            [
                "Add a professional email address.",
                "Optionally include a phone number and relevant professional profile link.",
            ],
            "name@example.com | +1 555 010 1234 | linkedin.com/in/name",
        ))

    if not resume_text.strip():
        return [
            _issue(
                "No resume text was extracted",
                "high",
                "The resume could not be assessed because no readable text was available.",
                "The uploaded document did not produce any extracted text.",
                "Uploaded document.",
                "Upload a text-based PDF or DOCX version of your resume.",
                ["Make sure the document contains selectable text."],
                "",
            )
        ]

    return issues


def generate_issues_summary(issues: List[IssueDetail]) -> List[str]:
    if not issues:
        return ["No major issues detected. Your resume is well-structured and clearly presented."]

    return [
        f"{issue.severity_level.title()}: {issue.issue_title}"
        for issue in issues[:5]
    ]
