from flask import Flask, request, render_template, redirect, url_for, flash
import os
import time
import json
import copy

from utils.stt import get_transcript
from utils.nlp import generate_summary, generate_minutes_of_meeting
from utils.nlp import transcribe_audio, format_transcript
from utils.email_utils import send_email
from utils.format_utils import format_mom_as_markdown
from utils.pdf_utils import create_mom_pdf
from db.supabase import add_meeting, add_meeting_minute, add_meeting_attendee

app = Flask(__name__)
app.secret_key = os.urandom(24)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@app.route('/', methods=['GET', 'POST'])
def upload_and_transcribe():
    """
    Upload Zoom video/audio file and generate transcript immediately.
    """
    if request.method == 'POST':
        if 'file' not in request.files or request.files['file'].filename == '':
            flash("Please select a video or audio file to upload.", 'error')
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

        try:
            transcript_text, transcript_json = transcribe_audio(local_path)
            formatted_transcript = format_transcript(transcript_json)
        except Exception as e:
            flash(f"Error processing transcription data: {e}", 'error')
            return render_template('transcribe.html')

        # Pass the uploaded video filename along for downstream use
        return render_template(
            'edit_transcription.html',
            transcription=formatted_transcript,
            uploaded_video=filename
        )

    return render_template('transcribe.html')


@app.route('/generate_mom', methods=['POST'])
def generate_mom():
    """
    Receive edited transcription and generate/display Meeting Summary & Minutes.
    """
    transcription = request.form.get('transcription', '').strip()
    uploaded_video = request.form.get('uploaded_video', '').strip()

    if not transcription:
        flash("Transcription cannot be empty.", 'error')
        return redirect(url_for('upload_and_transcribe'))

    # Generate summary and minutes of meeting using your NLP utils
    prompt = "Please summarize the following transcription:"
    summary = generate_summary(transcription, prompt)
    mom_dict = generate_minutes_of_meeting(transcription)
    mom_text = format_mom_as_markdown(mom_dict)
    print("Formatted mom_text:", repr(mom_text))

    # Pass mom_dict (dict) directly for template to serialize using |tojson
    return render_template('result.html',
                           transcription=transcription,
                           summary=summary,
                           mom=mom_text,
                           mom_json=mom_dict,     # pass dict, NOT JSON string
                           uploaded_video=uploaded_video)


@app.route('/finalize', methods=['POST'])
def finalize_and_share():
    """
    Receive finalized MoM, send emails, save data, and show success page.
    """
    transcription = request.form.get('transcription', '').strip()
    mom_text = request.form.get('mom', '').strip()
    mom_json_str = request.form.get('mom_json', '')
    summary = request.form.get('summary', '').strip()
    uploaded_video = request.form.get('uploaded_video', '').strip()  # If you want to keep track

    # Parse the MoM JSON (exactly once)
    try:
        mom_data_dict = json.loads(mom_json_str) if mom_json_str else {}
    except Exception as e:
        flash(f"Failed to parse Minutes of Meeting JSON: {e}", 'error')
        return redirect(url_for('upload_and_transcribe'))

    if not mom_text:
        flash("Minutes of Meeting cannot be empty.", 'error')
        return redirect(url_for('upload_and_transcribe'))

    recipient_emails = request.form.getlist('recipient_email')
    recipient_types = request.form.getlist('recipient_type')

    if not recipient_emails or not recipient_types or len(recipient_emails) != len(recipient_types):
        flash("Please provide valid recipients (email and type for each).", 'error')
        return redirect(url_for('upload_and_transcribe'))

    internal_members = []
    non_members = []
    recipients_info = []

    for email, typ in zip(recipient_emails, recipient_types):
        email = email.strip()
        if typ == 'internal':
            internal_members.append(email)
        else:
            non_members.append(email)
        recipients_info.append({
            "email": email,
            "type": typ,
            "sent_at": time.strftime("%Y-%m-%d %H:%M:%S")
        })

    if not internal_members and not non_members:
        flash("Please select at least one recipient.", 'error')
        return redirect(url_for('upload_and_transcribe'))

    # Generate PDFs
    pdf_buffer_internal = create_mom_pdf(mom_data_dict)
    customized_mom_dict = customize_mom_for_non_members(mom_data_dict)
    pdf_buffer_non_members = create_mom_pdf(customized_mom_dict)

    # Send emails
    for email in internal_members:
        send_email(
            to_email=email,
            subject="Minutes of Meeting",
            body="Please find the attached Minutes of Meeting.",
            pdf_buffer=pdf_buffer_internal
        )
        pdf_buffer_internal.seek(0)
    for email in non_members:
        send_email(
            to_email=email,
            subject="Customized Minutes of Meeting",
            body="Please find the customized Minutes of Meeting attached.",
            pdf_buffer=pdf_buffer_non_members
        )
        pdf_buffer_non_members.seek(0)

    # Save meeting and minutes data
    meeting_data = {
        "organization_id": "9a6ac03d-2a3e-42b3-9e1d-1047055cd7a9",
        "meeting_code": "AUTO-" + time.strftime("%Y%m%d%H%M%S"),
        "title": "Automated Meeting - " + time.strftime("%Y-%m-%d %H:%M"),
        "scheduled_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_mins": 60,
        "description": "Meeting created by automation",
    }
    meeting_result = add_meeting(meeting_data)
    if meeting_result:
        meeting_id = meeting_result[0]['id']

        minute_data = {
            "meeting_id": meeting_id,
            "full_mom": mom_text,
            "summary": summary,
            "transcript": transcription,
        }
        add_meeting_minute(minute_data)

        for recipient in recipients_info:
            attendee_data = {
                "meeting_id": meeting_id,
                "email": recipient["email"],
                "type": recipient["type"],
                "sent_at": recipient["sent_at"]
            }
            add_meeting_attendee(attendee_data)

    flash("Minutes of Meeting shared successfully with selected members.", "success")
    return render_template(
        'share_success.html',
        internal_members=internal_members,
        non_members=non_members
    )


def customize_mom_for_non_members(mom_dict):
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
                    filtered_subpoints = [
                        sp for sp in point.get('subpoints', [])
                        if not any(word in sp.lower() for word in sensitive_keywords)
                    ]
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


if __name__ == '__main__':
    app.run(debug=True, port=5001)
