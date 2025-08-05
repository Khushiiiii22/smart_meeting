from flask import Flask, request, render_template, redirect, url_for, flash
import os
import time
from utils.stt import get_transcript
from utils.nlp import generate_summary, generate_minutes_of_meeting  # we'll add this function
import config
from utils.nlp import transcribe_audio
from utils.nlp import format_transcript
from utils.email_utils import send_email
import json
from utils.format_utils import format_mom_as_markdown
from utils.pdf_utils import create_mom_pdf

from db.supabase import add_meeting, add_meeting_minute  # Import Supabase save functions



app = Flask(__name__)
app.secret_key = os.urandom(24)


UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@app.route('/', methods=['GET', 'POST'])
def upload_and_transcribe():
    if request.method == 'POST':
        if 'file' not in request.files or request.files['file'].filename == '':
            flash("Please select a file to upload.", 'error')
            return render_template('transcribe.html')


        file = request.files['file']
        filename = file.filename.replace(' ', '_')
        local_path = os.path.join(UPLOAD_FOLDER, filename)


        try:
            file.save(local_path)
        except Exception as e:
            flash(f"Failed to save the file: {e}", 'error')
            return render_template('transcribe.html')


        transcription = get_transcript(local_path)
        if not transcription:
            flash("Transcription failed. Please try again.", 'error')
            return render_template('transcribe.html')


        # Render a page showing editable transcription with form to submit for summary/MoM
        transcript_text, transcript_json = transcribe_audio(local_path)
        formatted_transcript = format_transcript(transcript_json)
        
        print("transcript_text:", repr(transcript_text))
        print("transcript_json:", transcript_json)
        print("formatted_transcript:", repr(formatted_transcript))
        return render_template('edit_transcription.html', transcription=formatted_transcript)


    return render_template('transcribe.html')


@app.route('/generate', methods=['POST'])
def generate_mom_summary():
    transcription = request.form.get('transcription')
    if not transcription or transcription.strip() == '':
        flash("Transcription text is empty. Please provide valid transcription.", 'error')
        return redirect(url_for('upload_and_transcribe'))


    mom = generate_minutes_of_meeting(transcription)  # markdown/plain text or dict depending on your function
    summary = generate_summary(transcription, "Provide a brief summary of this meeting.")


    if not summary:
        flash("Summary generation failed.", 'error')
        summary = ""


    if not mom:
        flash("Minutes of Meeting generation failed.", 'error')
        mom = ""


    # Pass example internal and external emails for selection on front-end (can be made dynamic)
    internal_members = ['internal1@example.com', 'internal2@example.com']
    non_members = ['external1@example.com']


    mom_json = generate_minutes_of_meeting(transcription)
    mom_markdown = format_mom_as_markdown(mom_json) if mom_json else ""


    return render_template('result.html',
                        transcription=transcription,
                        summary=summary,
                        mom=mom_markdown,
                        mom_json=mom_json,
                        internal_members=internal_members,
                        non_members=non_members)


# Your ReportLab based PDF generator from dict
def customize_mom_for_non_members(mom_dict):
    import copy
    redacted = copy.deepcopy(mom_dict)
    sensitive_keywords = ['confidential', 'internal', 'salary', 'budget']


    if 'agenda' in redacted and isinstance(redacted['agenda'], list):
        redacted['agenda'] = [item for item in redacted['agenda']
                             if not any(word in item.lower() for word in sensitive_keywords)]


    if 'discussions' in redacted and isinstance(redacted['discussions'], list):
        filtered_discussions = []
        for section in redacted['discussions']:
            filtered_points = []
            for point in section.get('points', []):
                if isinstance(point, dict):
                    text_lower = point.get('text', '').lower()
                    if any(word in text_lower for word in sensitive_keywords):
                        continue
                    filtered_subpoints = [sp for sp in point.get('subpoints', []) if not any(word in sp.lower() for word in sensitive_keywords)]
                    filtered_points.append({
                        'text': point.get('text', ''),
                        'subpoints': filtered_subpoints
                    })
                elif isinstance(point, str):
                    if any(word in point.lower() for word in sensitive_keywords):
                        continue
                    filtered_points.append(point)
                else:
                    filtered_points.append(point)
            section['points'] = filtered_points
            filtered_discussions.append(section)
        redacted['discussions'] = filtered_discussions


    return redacted


@app.route('/finalize', methods=['POST'])
def finalize_and_share():
    transcription = request.form.get('transcription', '').strip()
    mom_text = request.form.get('mom', '').strip()  # markdown text for display, not used for PDF generation
    
    mom_json_str = request.form.get('mom_json', '')
    try:
        mom_data_dict = json.loads(mom_json_str) if mom_json_str else {}
    except Exception as e:
        flash(f"Failed to parse Minutes of Meeting JSON: {e}", 'error')
        return redirect(url_for('upload_and_transcribe'))
    
    if not mom_text:
        flash("Minutes of Meeting cannot be empty.", 'error')
        return redirect(url_for('upload_and_transcribe'))
    
    internal_members = request.form.getlist('internal_members')
    non_members = request.form.getlist('non_members')
    
    if not internal_members and not non_members:
        flash("Please select at least one recipient.", 'error')
        return redirect(url_for('upload_and_transcribe'))
    print("[DEBUG] MoM dict for PDF generation:", mom_data_dict)


    # Generate PDF for internal members
    pdf_buffer_internal = create_mom_pdf(mom_data_dict)
    # Generate PDF for external members (redacted/customized)
    customized_mom_dict = customize_mom_for_non_members(mom_data_dict)
    pdf_buffer_non_members = create_mom_pdf(customized_mom_dict)
    
    # Send emails to internal members
    for email in internal_members:
        send_email(
            to_email=email,
            subject="Minutes of Meeting",
            body="Please find the attached Minutes of Meeting.",
            pdf_buffer=pdf_buffer_internal)
        pdf_buffer_internal.seek(0)
    
    # Send emails to non-members
    for email in non_members:
        send_email(
            to_email=email,
            subject="Customized Minutes of Meeting",
            body="Please find the customized Minutes of Meeting attached.",
            pdf_buffer=pdf_buffer_non_members)
        pdf_buffer_non_members.seek(0)

    # --- SAVE TO SUPABASE ---
    meeting_data = {
        "organization_id": "9a6ac03d-2a3e-42b3-9e1d-1047055cd7a9",  # Example, replace with actual ID
        "meeting_code": "AUTO-" + time.strftime("%Y%m%d%H%M%S"),  # unique code example
        "title": "Automated Meeting - " + time.strftime("%Y-%m-%d %H:%M"),
        "scheduled_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_mins": 60,  # example duration, you can set dynamically
        "description": "Meeting created by automation",
    }

    meeting_result = add_meeting(meeting_data)
    if meeting_result:
        meeting_id = meeting_result[0]['id']
        minute_data = {
            "meeting_id": meeting_id,
            "full_mom": mom_text,
            "summary": request.form.get('summary', '').strip(),
            "transcript": transcription,
        }


        add_meeting_minute(minute_data)
    # --- END SUPABASE LOGIC ---

    flash("Minutes of Meeting shared successfully with selected members.", "success")
    return render_template('share_success.html',
                       internal_members=internal_members,
                       non_members=non_members)




if __name__ == '__main__':
    app.run(debug=True, port=5001)
