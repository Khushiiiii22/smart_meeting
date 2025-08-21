from flask import Flask, render_template, request
import markdown

app = Flask(__name__)

def format_mom_as_markdown(mom):
    lines = []

    # Header
    lines.append("## Minutes of Meeting (MoM)\n")
    lines.append(f"**Meeting Title:** {mom.get('title', 'N/A')}")
    date = mom.get('date', '')
    time = mom.get('time', '')
    dt_line = ""
    if date:
        dt_line += f"{date}"
    if time:
        dt_line += f" - {time}" if dt_line else time
    if dt_line:
        lines.append(f"**Date & Time:** {dt_line}")
    venue = mom.get('venue', '')
    if venue:
        lines.append(f"**Venue:** {venue}")

    # Attendees
    attendees = mom.get('attendees', [])
    lines.append("**Attendees:**")
    if attendees:
        for att in attendees:
            lines.append(f"*   {att}")
    else:
        lines.append("No attendees listed.")

    lines.append("---\n")

    # Purpose
    purpose = mom.get('purpose', '')
    if purpose:
        lines.append("### **1. Purpose of Meeting**")
        lines.append(purpose + "\n")
    else:
        lines.append("### **1. Purpose of Meeting**")
        lines.append("No purpose specified.\n")

    # Discussions
    discussions = mom.get('discussions', [])
    if discussions:
        lines.append("### **2. Key Discussion Points**\n")
        for idx, section in enumerate(discussions, start=1):
            sec_title = section.get('section_title', f"Section {idx}")
            lines.append(f"**2.{idx} {sec_title}:**\n")
            points = section.get('points', [])
            for point in points:
                if isinstance(point, dict):
                    text = point.get('text', '')
                    if text:
                        lines.append(text.strip() + " ")
                    subpoints = point.get('subpoints', [])
                    for sp in subpoints:
                        lines.append(sp.strip() + " ")
                else:
                    lines.append(point.strip() + " ")
            lines.append("")
    else:
        lines.append("### **2. Key Discussion Points**")
        lines.append("No discussion points available.\n")

    # Decisions
    decisions = mom.get('decisions', [])
    lines.append("### **3. Decisions**")
    if decisions:
        for decision in decisions:
            lines.append(f"*   {decision}")
    else:
        lines.append("No formal decisions were made during this meeting.")
    lines.append("")

    # Action Items
    action_items = mom.get('action_items', [])
    if action_items:
        lines.append("### **4. Action Items**\n")
        lines.append("| Action Item | Owner | Status | Notes |")
        lines.append("| :---------- | :---- | :----- | :---- |")
        for action in action_items:
            item = action.get('item', '')
            owner = action.get('owner', '')
            status = action.get('status', '')
            notes = action.get('notes', '')
            lines.append(f"| {item} | {owner} | {status} | {notes} |")
        lines.append("")
    else:
        lines.append("### **4. Action Items**")
        lines.append("No action items assigned.\n")

    # Next Steps
    next_steps = mom.get('next_steps', [])
    if next_steps:
        lines.append("### **5. Next Steps**")
        for step in next_steps:
            lines.append(f"*   {step}")
        lines.append("")
    else:
        lines.append("### **5. Next Steps**")
        lines.append("No next steps specified.\n")

    # Footer
    prepared_by = mom.get('prepared_by', '')
    prep_date = mom.get('preparation_date', '')
    lines.append("---")
    if prepared_by:
        lines.append(f"**Minutes Prepared By:** {prepared_by}")
    if prep_date:
        lines.append(f"**Date of Preparation:** {prep_date}")

    return '\n'.join(lines)

@app.route('/mom_view', methods=['GET', 'POST'])
def mom_view():
    # Example mom data (replace with real dynamic data)
    mom_data = {
        "title": "Team Sync-up",
        "date": "2025-08-20",
        "time": "10:00 AM",
        "venue": "Conference Room A",
        "attendees": ["Alice", "Bob", "Charlie"],
        "purpose": "Discuss project updates and next steps.",
        "discussions": [
            {"section_title": "Project Updates", "points": ["Finished phase 1", "Delayed module integration"]},
            {"section_title": "Challenges", "points": ["Resource constraints", "Pending approvals"]}
        ],
        "decisions": ["Approved new timeline", "Allocate more developers"],
        "action_items": [
            {"item": "Complete testing", "owner": "Alice", "status": "In Progress", "notes": ""},
            {"item": "Prepare report", "owner": "Bob", "status": "Pending", "notes": "Due next week"},
        ],
        "next_steps": ["Schedule follow-up", "Notify stakeholders"],
        "prepared_by": "Project Manager",
        "preparation_date": "2025-08-20"
    }

    markdown_text = format_mom_as_markdown(mom_data)

    # Convert markdown to HTML for preview
    html_preview = markdown.markdown(markdown_text)

    return render_template('mom_view.html', formatted_mom=markdown_text, html_preview=html_preview)
