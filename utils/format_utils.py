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
            # Join all points in the section as separate sentences instead of bullets
            for point in points:
                if isinstance(point, dict):  # If point is dict with complex structure
                    text = point.get('text', '')
                    if text:
                        lines.append(text.strip() + " ")
                    subpoints = point.get('subpoints', [])
                    for sp in subpoints:
                        lines.append(sp.strip() + " ")
                else:
                    lines.append(point.strip() + " ")
            lines.append("")  # blank line after each section
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
