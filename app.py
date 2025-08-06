from flask import Flask, request, render_template, redirect, url_for, flash
import os
import time
import json
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
    Upload Zoom video file.
    """
    if request.method == 'POST':
        if 'file' not in request.files or request.files['file'].filename == '':
            flash("Please select a video file to upload.", 'error')
            return render_template('upload_video.html')

        file = request.files['file']
        filename = file.filename.replace(' ', '_')
        local_path = os.path.join(UPLOAD_FOLDER, filename)

        try:
            file.save(local_path)
        except Exception as e:
            flash(f"Failed to save the file: {e}", 'error')
            return render_template('upload_video.html')

        flash("Video uploaded successfully! Now you can generate the transcript.", "success")
        # Pass the uploaded file path for next step if you want
        return render_template('upload_video.html', uploaded_video=filename)

    return render_template('upload_video.html')


@app.route('/generate', methods=['POST'])
def generate_transcript():
    """
    Generate transcript from uploaded Zoom video file.
    """
    filename = request.form.get('uploaded_video')
    if not filename:
        flash("No uploaded video specified. Please upload a video first.", 'error')
        return redirect(url_for('upload_zoom_video'))

    local_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(local_path):
        flash("Uploaded video file not found. Please upload again.", 'error')
        return redirect(url_for('upload_zoom_video'))

    # Generate transcription using your existing utils
    transcription = get_transcript(local_path)
    if not transcription:
        flash("Transcription failed. Please try again.", 'error')
        return redirect(url_for('upload_zoom_video'))

    # Optionally get more structured transcript info
    transcript_text, transcript_json = transcribe_audio(local_path)
    formatted_transcript = format_transcript(transcript_json)

    print("transcript_text:", repr(transcript_text))
    print("transcript_json:", transcript_json)
    print("formatted_transcript:", repr(formatted_transcript))

    # Render page where user can edit transcription and continue to generate MoM
    return render_template('edit_transcription.html', transcription=formatted_transcript)


@app.route('/finalize', methods=['POST'])
def finalize_and_share():
    """
    Finalize Minutes of Meeting and share via email and save to database.
    (Same as your existing finalize implementation)
    """
    transcription = request.form.get('transcription', '').strip()
    mom_text = request.form.get('mom', '').strip()
    mom_json_str = request.form.get('mom_json', '')
    summary = request.form.get('summary', '').strip()

    # Parse the MoM JSON
    try:
        mom_data_dict = json.loads(mom_json_str) if mom_json_str else {}
    except Exception as e:
        flash(f"Failed to parse Minutes of Meeting JSON: {e}", 'error')
        return redirect(url_for('upload_zoom_video'))

    if not mom_text:
        flash("Minutes of Meeting cannot be empty.", 'error')
        return redirect(url_for('upload_zoom_video'))

    recipient_emails = request.form.getlist('recipient_email')
    recipient_types = request.form.getlist('recipient_type')

    if not recipient_emails or not recipient_types or len(recipient_emails) != len(recipient_types):
        flash("Please provide valid recipients (email and type for each).", 'error')
        return redirect(url_for('upload_zoom_video'))

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
        return redirect(url_for('upload_zoom_video'))

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
