import os
import cv2
import smtplib
from email.message import EmailMessage
from flask import Flask, render_template, request, url_for


app = Flask(__name__)

# ---------------- CONFIG ----------------
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Temporary user data storage (for demo)
user_data = {}

# Load face detection model
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

# ---------------- ROUTES ----------------

# Home page
@app.route('/')
def index():
    return render_template('upload.html')


# Upload image + user details

@app.route('/upload', methods=['POST'])
def upload():
    username = request.form.get('username')
    email = request.form.get('email')
    file = request.files.get('photo')

    if not file:
        return "No file uploaded"

    filename = file.filename
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(save_path)

    # Store user details
    user_data['name'] = username
    user_data['email'] = email
    user_data['photo'] = filename

    # ---------- FACE DETECTION ----------
    img = cv2.imread(save_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    if len(faces) == 0:
        return "No face detected"

    # ---------- FACIAL LOCK CREATION 🔐 ----------
    (x, y, w, h) = faces[0]      # TAKE FIRST FACE
    face_img = gray[y:y+h, x:x+w]
    cv2.imwrite("static/locked_face.jpg", face_img)

    image_url = url_for('static', filename='uploads/' + filename)

    return render_template(
        'result.html',
        image_url=image_url,
        message="Face detected – Facial lock created 🔐"
    )
#-----------Simulate deepfake------------

@app.route('/deepfake_attempt', methods=['GET', 'POST'])
def deepfake_attempt():

    # Show upload page
    if request.method == 'GET':
        return render_template('deepfake.html')

    # Handle deepfake attempt upload
    if 'photo' not in request.files:
        return "No deepfake image uploaded"

    file = request.files['photo']
    path = "static/attempt.jpg"
    file.save(path)

    attempt_img = cv2.imread(path, 0)
    locked_img = cv2.imread("static/locked_face.jpg", 0)

    if locked_img is None:
        return "Facial lock not found. Please upload original photo first."

    # Detect face in attempt image
    attempt_faces = face_cascade.detectMultiScale(attempt_img, 1.3, 5)

    if len(attempt_faces) == 0:
        return "No face detected in deepfake attempt image"

    (x, y, w, h) = attempt_faces[0]
    attempt_face_img = attempt_img[y:y+h, x:x+w]

    # Resize for comparison
    attempt_face_img = cv2.resize(attempt_face_img, (200, 200))
    locked_img = cv2.resize(locked_img, (200, 200))

    # Compare faces (simulation)
    similarity = cv2.norm(locked_img, attempt_face_img, cv2.NORM_L2)

    if similarity < 3000:
        send_consent_email(user_data['email'], user_data['name'])
        return render_template(
            'consent.html',
            email=user_data['email']
        )
    else:
        return "Face does not match. No consent required."



# Handle consent decision
@app.route('/consent_action', methods=['POST'])
def consent_action():
    decision = request.form.get('decision')

    if decision == 'approve':
        result = "Consent Approved"
        message = "Deepfake generation is allowed."
    else:
        result = "Consent Denied"
        message = "Deepfake attempt has been blocked."

    return render_template(
        'final.html',
        result=result,
        message=message
    )

sender_email ="shruthi310504@gmail.com"
app_password = "qisexnyvooulplec"



def send_consent_email(receiver_email, username):
    allow_link = "http://127.0.0.1:5000/consent/allow"
    deny_link = "http://127.0.0.1:5000/consent/deny"

    body = f"""
Hello {username},

⚠️ A deepfake attempt was detected using your photo.

Someone is trying to generate or edit your image.
Your approval is required to continue.

Please choose one option below:

ALLOW deepfake generation:
{allow_link}

DENY deepfake generation:
{deny_link}

If you did not request this action, please deny immediately.

Thank you,
AI Consent Driven Photo Security Platform
"""

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = "Deepfake Attempt Detected – Consent Required"
    msg["From"] = sender_email
    msg["To"] = receiver_email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, app_password)
        server.send_message(msg)
@app.route('/consent/allow')
def consent_allow():
    user_data['consent'] = 'approved'
    return render_template(
        'final.html',
        result="Consent Approved",
        message="Deepfake generation is allowed."
    )


@app.route('/consent/deny')
def consent_deny():
    user_data['consent'] = 'denied'
    return render_template(
        'final.html',
        result="Consent Denied",
        message="Deepfake attempt blocked for security reasons."
    )


# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)


