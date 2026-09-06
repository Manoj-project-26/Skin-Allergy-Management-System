from flask import Flask, render_template, request, session
import sqlite3
from urllib.parse import quote
from reportlab.lib.pagesizes import A4
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "skin_allergy_secret_key"
def create_database():
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    # -----------------------------
    # Users Table
    # -----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # -----------------------------
    # Patients Table
    # -----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            symptoms TEXT NOT NULL,
            allergy_history TEXT
        )
    """)

    # -----------------------------
    # Add user_id column
    # -----------------------------
    try:
        cursor.execute(
            "ALTER TABLE patients ADD COLUMN user_id INTEGER"
        )
    except sqlite3.OperationalError:
        pass

    # -----------------------------
    # Add AI Analysis columns
    # -----------------------------
    try:
        cursor.execute(
            "ALTER TABLE patients ADD COLUMN skin_area TEXT"
        )
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE patients ADD COLUMN duration TEXT"
        )
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE patients ADD COLUMN additional_info TEXT"
        )
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE patients ADD COLUMN condition TEXT"
        )
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE patients ADD COLUMN guidance TEXT"
        )
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute(
            "ALTER TABLE patients ADD COLUMN doctor TEXT"
        )
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE patients ADD COLUMN reason TEXT"
        )
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE patients ADD COLUMN doctor_duration TEXT"
        )
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE patients ADD COLUMN doctor_symptoms TEXT"
        )
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE patients ADD COLUMN doctor_additional_info TEXT"
        )
    except sqlite3.OperationalError:
        pass
            # Hospital Location columns

    try:
        cursor.execute(
            "ALTER TABLE patients ADD COLUMN hospital_location TEXT"
        )
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE patients ADD COLUMN hospitals TEXT"
        )
    except sqlite3.OperationalError:
        pass

    connection.commit()
    connection.close()


@app.route("/")
def home():
    return render_template("home.html")
@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return "Passwords do not match!"

        connection = sqlite3.connect("database.db")
        cursor = connection.cursor()

        try:
            cursor.execute("""
                INSERT INTO users (name, email, phone, password)
                VALUES (?, ?, ?, ?)
            """, (name, email, phone, password))

            connection.commit()

        except sqlite3.IntegrityError:
            connection.close()
            return "Email already registered!"

        connection.close()

        return "Registration Successful!"

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = sqlite3.connect("database.db")
        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email = ? AND password = ?",
            (email, password)
        )

        user = cursor.fetchone()

        connection.close()

        if user:

            # Start completely fresh session for new login
            session.clear()

            session["user_id"] = user[0]

            # Fresh report status
            session["patient_done"] = False
            session["ai_done"] = False
            session["doctor_done"] = False
            session["hospital_done"] = False

            return render_template("dashboard.html")

        return "Invalid Email or Password!"

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")
@app.route("/logout")
def logout():
    session.clear()
    return render_template("login.html")
@app.route("/patient-details", methods=["GET", "POST"])
def patient_details():

    if "user_id" not in session:
        return render_template("login.html")

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    if request.method == "POST":

        patient_name = request.form["patient_name"]
        age = request.form["age"]
        gender = request.form["gender"]
        phone = request.form["phone"]
        address = request.form["address"]

        symptoms_list = request.form.getlist("symptoms")
        symptoms = ", ".join(symptoms_list)

        allergy_history = request.form.get("allergy_history", "")

        cursor.execute("""
            INSERT INTO patients
            (patient_name, age, gender, phone, address,
             symptoms, allergy_history, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            patient_name,
            age,
            gender,
            phone,
            address,
            symptoms,
            allergy_history,
            session["user_id"]
        ))

        connection.commit()

        session["patient_done"] = True
        session["ai_done"] = False
        session["doctor_done"] = False
        session["hospital_done"] = False

    # Get the current user's latest patient details
    cursor.execute("""
        SELECT patient_name, age, gender, phone, address,
               symptoms, allergy_history
        FROM patients
        WHERE user_id = ?
        ORDER BY rowid DESC
        LIMIT 1
    """, (session["user_id"],))

    patient = cursor.fetchone()

    connection.close()

    return render_template(
        "patient_details.html",
        patient=patient
    )
@app.route("/ai-allergy", methods=["GET", "POST"])
def ai_allergy():

    if request.method == "POST":

        # Check whether user is logged in
        if "user_id" not in session:
            return "Please login first."

        skin_area = request.form["skin_area"]
        duration = request.form["duration"]

        # Get all selected symptoms from checkboxes
        symptoms_list = request.form.getlist("symptoms")
        symptoms = " ".join(symptoms_list).lower()

        additional_info = request.form.get(
            "additional_info",
            ""
        )

        # -----------------------------------------
        # Simple rule-based preliminary analysis
        # -----------------------------------------

        if ("itching" in symptoms and
                "redness" in symptoms and
                "rash" in symptoms):

            condition = "Possible Allergic Skin Reaction"

            guidance = (
                "Avoid possible irritants and consult a qualified "
                "healthcare professional."
            )

        elif "itching" in symptoms and "hives" in symptoms:

            condition = "Possible Hives / Urticaria"

            guidance = (
                "Avoid suspected triggers and consult a qualified "
                "healthcare professional."
            )

        elif "redness" in symptoms and "swelling" in symptoms:

            condition = "Possible Allergic Reaction"

            guidance = (
                "Seek professional medical evaluation, especially "
                "if symptoms are severe."
            )

        elif "itching" in symptoms:

            condition = "Possible Skin Irritation"

            guidance = (
                "Avoid possible irritants and consult a qualified "
                "healthcare professional if symptoms persist."
            )

        elif "redness" in symptoms:

            condition = "Possible Skin Irritation"

            guidance = (
                "Avoid possible irritants and consult a qualified "
                "healthcare professional."
            )

        elif "rash" in symptoms:

            condition = "Possible Skin Irritation"

            guidance = (
                "Avoid suspected irritants and seek professional "
                "advice if symptoms continue."
            )

        elif "dryness" in symptoms:

            condition = "Possible Dry Skin Irritation"

            guidance = (
                "Use gentle skin care and consult a healthcare "
                "professional if symptoms persist."
            )

        elif "swelling" in symptoms:

            condition = "Possible Allergic Reaction"

            guidance = (
                "Seek professional medical evaluation, especially "
                "if swelling is severe or increasing."
            )

        elif "burning" in symptoms:

            condition = "Possible Skin Irritation"

            guidance = (
                "Avoid products that may irritate the skin and "
                "consider professional evaluation."
            )

        elif "irritation" in symptoms:

            condition = "Possible Skin Irritation"

            guidance = (
                "Avoid suspected irritants and consult a healthcare "
                "professional if symptoms continue."
            )

        elif "bumps" in symptoms:

            condition = "Possible Skin Irritation"

            guidance = (
                "Avoid suspected irritants and consult a healthcare "
                "professional if symptoms continue."
            )

        elif "blisters" in symptoms:

            condition = "Possible Skin Reaction"

            guidance = (
                "Avoid touching or irritating the affected area "
                "and seek professional medical evaluation."
            )

        elif "peeling" in symptoms:

            condition = "Possible Dry or Irritated Skin"

            guidance = (
                "Use gentle skin care and consult a healthcare "
                "professional if symptoms persist."
            )

        elif "cracked" in symptoms:

            condition = "Possible Dry Skin Irritation"

            guidance = (
                "Keep the skin moisturized and consult a healthcare "
                "professional if the condition continues."
            )

        elif "scaling" in symptoms:

            condition = "Possible Scaling Skin Condition"

            guidance = (
                "Avoid harsh skin products and seek professional "
                "medical advice for proper evaluation."
            )

        elif "hives" in symptoms:

            condition = "Possible Hives / Urticaria"

            guidance = (
                "Avoid suspected triggers and consult a qualified "
                "healthcare professional."
            )

        elif "oozing" in symptoms:

            condition = "Possible Skin Condition Requiring Evaluation"

            guidance = (
                "Oozing or fluid discharge should be evaluated by "
                "a qualified healthcare professional."
            )

        elif "flaking" in symptoms:

            condition = "Possible Dry Skin Irritation"

            guidance = (
                "Use gentle skin care and consult a healthcare "
                "professional if symptoms persist."
            )

        elif "warmth" in symptoms:

            condition = "Possible Skin Inflammation"

            guidance = (
                "Skin warmth may be associated with inflammation. "
                "Please consult a healthcare professional."
            )

        elif "tenderness" in symptoms:

            condition = "Possible Skin Inflammation"

            guidance = (
                "Please consult a qualified healthcare professional "
                "if tenderness persists or increases."
            )

        elif "tightness" in symptoms:

            condition = "Possible Dry or Irritated Skin"

            guidance = (
                "Use gentle skin care and consult a healthcare "
                "professional if symptoms persist."
            )

        elif "discoloration" in symptoms:

            condition = "Possible Skin Discoloration"

            guidance = (
                "Skin discoloration can have different causes. "
                "Please consult a qualified healthcare professional."
            )

        elif "pain" in symptoms:

            condition = "Possible Skin Inflammation"

            guidance = (
                "Please consult a qualified healthcare professional, "
                "especially if pain increases."
            )

        else:

            condition = "Unclassified Skin Symptoms"

            guidance = (
                "Please consult a qualified healthcare professional "
                "for proper evaluation."
            )

        # -----------------------------------------
        # Save AI result for the current user
        # -----------------------------------------

        connection = sqlite3.connect("database.db")
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id
            FROM patients
            WHERE user_id = ?
            ORDER BY rowid DESC
            LIMIT 1
        """, (session["user_id"],))

        patient = cursor.fetchone()

        if patient:

            # Update existing patient's latest record
            cursor.execute("""
                UPDATE patients
                SET skin_area = ?,
                    duration = ?,
                    additional_info = ?,
                    condition = ?,
                    guidance = ?
                WHERE id = ?
            """, (
                skin_area,
                duration,
                additional_info,
                condition,
                guidance,
                patient[0]
            ))

        else:

            # If patient details were not saved yet,
            # create a basic patient record
            cursor.execute("""
                INSERT INTO patients
                (
                    patient_name,
                    age,
                    gender,
                    phone,
                    address,
                    symptoms,
                    allergy_history,
                    user_id,
                    skin_area,
                    duration,
                    additional_info,
                    condition,
                    guidance
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "Not Provided",
                0,
                "Not Provided",
                "Not Provided",
                "Not Provided",
                symptoms,
                "",
                session["user_id"],
                skin_area,
                duration,
                additional_info,
                condition,
                guidance
            ))

        connection.commit()
        connection.close()

        # -----------------------------------------
        # Also keep result in session
        # for current report page
        # -----------------------------------------

        session["skin_area"] = skin_area
        session["duration"] = duration
        session["symptoms"] = symptoms
        session["additional_info"] = additional_info
        session["condition"] = condition
        session["guidance"] = guidance
        session["ai_done"] = True

        # -----------------------------------------
        # Display result
        # -----------------------------------------

        return f"""
        <h1>🤖 AI Skin Allergy Analysis</h1>

        <h2>Analysis Result</h2>

        <p><b>Skin Area:</b> {skin_area}</p>

        <p><b>Duration:</b> {duration}</p>

        <p><b>Symptoms:</b> {symptoms}</p>

        <p><b>Additional Information:</b> {additional_info}</p>

        <h3>Possible Condition</h3>

        <p>{condition}</p>

        <h3>Basic Guidance</h3>

        <p>{guidance}</p>

        <p>
            ⚠️ This is a project-based preliminary result and
            not a medical diagnosis.
        </p>

        <a href="/ai-allergy">Analyze Again</a>

        <br><br>

        <a href="/dashboard">Back to Dashboard</a>
        """

    return render_template("ai_allergy.html")
@app.route("/doctor-suggestion", methods=["GET", "POST"])
def doctor_suggestion():

    # Check whether user is logged in
    if "user_id" not in session:
        return "Please login first."

    if request.method == "POST":

        symptoms_list = request.form.getlist("symptoms")
        symptoms = ", ".join(symptoms_list).lower()

        duration = request.form["duration"]

        additional_info = request.form.get(
            "additional_info",
            ""
        )

        # -----------------------------------------
        # Doctor Suggestion Rules
        # -----------------------------------------

        if "itching" in symptoms and "rash" in symptoms:

            doctor = "Dermatologist"

            reason = (
                "A dermatologist can evaluate skin rashes "
                "and itching."
            )

        elif "redness" in symptoms and "swelling" in symptoms:

            doctor = "Dermatologist"

            reason = (
                "A dermatologist can evaluate skin redness "
                "and swelling."
            )

        elif "dry" in symptoms or "dryness" in symptoms:

            doctor = "Dermatologist"

            reason = (
                "A dermatologist can evaluate persistent dry "
                "or irritated skin."
            )

        else:

            doctor = "Dermatologist"

            reason = (
                "A dermatologist is the appropriate specialist "
                "for skin-related concerns."
            )

        # -----------------------------------------
        # Find latest patient of current user
        # -----------------------------------------

        connection = sqlite3.connect("database.db")
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id
            FROM patients
            WHERE user_id = ?
            ORDER BY rowid DESC
            LIMIT 1
        """, (session["user_id"],))

        patient = cursor.fetchone()

        # -----------------------------------------
        # Save Doctor Suggestion
        # -----------------------------------------

        if patient:

            cursor.execute("""
                UPDATE patients
                SET doctor = ?,
                    reason = ?,
                    doctor_duration = ?,
                    doctor_symptoms = ?,
                    doctor_additional_info = ?
                WHERE id = ?
            """, (
                doctor,
                reason,
                duration,
                symptoms,
                additional_info,
                patient[0]
            ))

        else:

            # If patient details are not available,
            # create a basic patient record
            cursor.execute("""
                INSERT INTO patients
                (
                    patient_name,
                    age,
                    gender,
                    phone,
                    address,
                    symptoms,
                    allergy_history,
                    user_id,
                    doctor,
                    reason,
                    doctor_duration,
                    doctor_symptoms,
                    doctor_additional_info
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "Not Provided",
                0,
                "Not Provided",
                "Not Provided",
                "Not Provided",
                symptoms,
                "",
                session["user_id"],
                doctor,
                reason,
                duration,
                symptoms,
                additional_info
            ))

        connection.commit()
        connection.close()

        # -----------------------------------------
        # Also store in session
        # -----------------------------------------

        session["doctor_done"] = True
        session["doctor"] = doctor
        session["reason"] = reason
        session["doctor_duration"] = duration
        session["doctor_symptoms"] = symptoms
        session["doctor_additional_info"] = additional_info

        # -----------------------------------------
        # Display Result
        # -----------------------------------------

        return f"""
        <h1>👨‍⚕️ Doctor Suggestion</h1>

        <h2>Suggested Specialist</h2>

        <p>
            <b>Doctor Type:</b> {doctor}
        </p>

        <p>
            <b>Reason:</b> {reason}
        </p>

        <p>
            <b>Duration:</b> {duration}
        </p>

        <p>
            <b>Symptoms:</b> {symptoms}
        </p>

        <p>
            <b>Additional Information:</b> {additional_info}
        </p>

        <p>
        ⚠️ This is a project-based suggestion and not a
        medical diagnosis.
        Please consult a qualified healthcare professional.
        </p>

        <a href="/doctor-suggestion">Check Again</a>

        <br><br>

        <a href="/dashboard">Back to Dashboard</a>
        """

    return render_template("doctor_suggestion.html")
@app.route("/hospital-location", methods=["GET", "POST"])
def hospital_location():

    # Check whether user is logged in
    if "user_id" not in session:
        return "Please login first."

    if request.method == "POST":

        location = request.form.get(
            "location", ""
        ).strip().lower()

        # -----------------------------------------
        # Hospital list based on location
        # -----------------------------------------

        if location == "chennai":

            hospitals = [
                "Government General Hospital - Chennai",
                "Rajiv Gandhi Government General Hospital - Chennai",
                "Government Stanley Hospital - Chennai"
            ]

        elif location == "coimbatore":

            hospitals = [
                "Coimbatore Medical College Hospital",
                "Government Hospital - Coimbatore"
            ]

        elif location == "madurai":

            hospitals = [
        "Government Rajaji Hospital, Madurai",
        "AIIMS Madurai",
        "Apollo Speciality Hospitals, Madurai",
        "Meenakshi Mission Hospital & Research Centre, Madurai",
        "Vadamalayan Hospitals, Madurai",
        "Velammal Medical College Hospital, Madurai",
        "Devadoss Hospital, Madurai",
        "Arun Hospital, Madurai",
        "Bharathi Hospital, Madurai",
        "Devaki Speciality Hospital, Madurai",
        "Iniya Multispeciality Hospital, Madurai",
        "Preethi Multispeciality Hospital, Madurai"
    ]
        else:

            hospitals = [
                "No hospital information available for this location in the demo."
            ]

        # -----------------------------------------
        # Convert hospital list to text
        # for SQLite storage
        # -----------------------------------------

        hospitals_text = " | ".join(hospitals)

        # -----------------------------------------
        # Find latest patient of current user
        # -----------------------------------------

        connection = sqlite3.connect("database.db")
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id
            FROM patients
            WHERE user_id = ?
            ORDER BY rowid DESC
            LIMIT 1
        """, (session["user_id"],))

        patient = cursor.fetchone()

        # -----------------------------------------
        # Save hospital information
        # -----------------------------------------

        if patient:

            cursor.execute("""
                UPDATE patients
                SET hospital_location = ?,
                    hospitals = ?
                WHERE id = ?
            """, (
                location.title(),
                hospitals_text,
                patient[0]
            ))

        else:

            # If patient details are not available,
            # create a basic patient record

            cursor.execute("""
                INSERT INTO patients
                (
                    patient_name,
                    age,
                    gender,
                    phone,
                    address,
                    symptoms,
                    allergy_history,
                    user_id,
                    hospital_location,
                    hospitals
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "Not Provided",
                0,
                "Not Provided",
                "Not Provided",
                "Not Provided",
                "",
                "",
                session["user_id"],
                location.title(),
                hospitals_text
            ))

        connection.commit()
        connection.close()

        # -----------------------------------------
        # Also save in session
        # -----------------------------------------

        session["hospital_done"] = True
        session["hospital_location"] = location.title()
        session["hospitals"] = hospitals

        # -----------------------------------------
        # Display hospital list
        # -----------------------------------------

        hospital_list = ""

        for hospital in hospitals:

            map_url = (
                "https://www.google.com/maps/search/?api=1&query="
                + quote(hospital + ", " + location.title() + ", Tamil Nadu")
            )

            hospital_list += f"""
            <li style="margin-bottom: 15px;">
                <b>{hospital}</b>
                <br>
                <a href="{map_url}" target="_blank">
                    📍 View on Google Maps
                </a>
            </li>
            """

        return f"""
        <h1>🏥 Hospital Information</h1>

        <h2>Location: {location.title()}</h2>

        <h3>Available Hospitals</h3>

        <ul>
            {hospital_list}
        </ul>

        <p>
        ⚠️ This hospital information is for project
        demonstration purposes.
        Please verify hospital details before visiting.
        </p>

        <a href="/hospital-location">Search Again</a>

        <br><br>

        <a href="/dashboard">Back to Dashboard</a>
        """
        return f"""    
        <h1>🏥 Hospital Information</h1>

        <h2>Location: {location.title()}</h2>

        <h3>Available Hospitals</h3>

        <ul>
            {hospital_list}
        </ul>

        <p>
        ⚠️ This hospital information is for project
        demonstration purposes.
        Please verify hospital details before visiting.
        </p>

        <a href="/hospital-location">Search Again</a>

        <br><br>

        <a href="/dashboard">Back to Dashboard</a>
        """

    return render_template("hospital_location.html")
@app.route("/report")
def report():

    if "user_id" not in session:
        return render_template("login.html")

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            patient_name,
            age,
            gender,
            phone,
            address,
            symptoms,
            allergy_history,

            skin_area,
            duration,
            condition,
            guidance,

            doctor,
            reason,
            doctor_duration,
            doctor_symptoms,
            doctor_additional_info,

            hospital_location,
            hospitals

        FROM patients
        WHERE user_id = ?
        ORDER BY rowid DESC
        LIMIT 1
    """, (session["user_id"],))

    patient = cursor.fetchone()

    connection.close()

    # -----------------------------------------
    # Default values
    # -----------------------------------------

    patient_done = False
    ai_done = False
    doctor_done = False
    hospital_done = False

    patient_name = "-"
    age = "-"
    gender = "-"
    phone = "-"
    address = "-"
    symptoms = "-"
    allergy_history = "-"

    skin_area = "-"
    duration = "-"
    condition = "-"
    guidance = "Please consult a qualified healthcare professional."

    doctor = "-"
    reason = "-"

    location = "-"
    hospitals = []

    # -----------------------------------------
    # Get saved data from database
    # -----------------------------------------

    if patient:

        patient_name = patient[0]
        age = patient[1]
        gender = patient[2]
        phone = patient[3]
        address = patient[4]
        symptoms = patient[5]
        allergy_history = patient[6]

        skin_area = patient[7] or "-"
        duration = patient[8] or "-"
        condition = patient[9] or "-"
        guidance = patient[10] or guidance

        doctor = patient[11] or "-"
        reason = patient[12] or "-"

        location = patient[16] or "-"

        if patient[17]:
            hospitals = patient[17].split(" | ")

        # -----------------------------------------
        # Module completion status
        # -----------------------------------------

        patient_done = True

        if patient[7] or patient[9]:
            ai_done = True

        if patient[11] or patient[12]:
            doctor_done = True

        if patient[16] or patient[17]:
            hospital_done = True

    # -----------------------------------------
    # Send data to report.html
    # -----------------------------------------

    return render_template(
        "report.html",

        # Patient
        patient_done=patient_done,
        patient_name=patient_name,
        age=age,
        gender=gender,
        phone=phone,
        address=address,
        symptoms=symptoms,
        allergy_history=allergy_history,

        # AI
        ai_done=ai_done,
        skin_area=skin_area,
        duration=duration,
        condition=condition,
        guidance=guidance,

        # Doctor
        doctor_done=doctor_done,
        doctor=doctor,
        reason=reason,

        # Hospital
        hospital_done=hospital_done,
        location=location,
        hospitals=hospitals
    )
@app.route("/download-report")
def download_report():

    if "user_id" not in session:
        return render_template("login.html")

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            patient_name,
            age,
            gender,
            phone,
            address,
            symptoms,
            allergy_history,
            skin_area,
            duration,
            condition,
            guidance,
            doctor,
            reason,
            hospital_location,
            hospitals
        FROM patients
        WHERE user_id = ?
        ORDER BY rowid DESC
        LIMIT 1
    """, (session["user_id"],))

    patient = cursor.fetchone()

    connection.close()

    buffer = BytesIO()

    pdf = SimpleDocTemplate(
        buffer,
        pagesize=A4
    )

    styles = getSampleStyleSheet()
    story = []

    story.append(
        Paragraph("Skin Allergy Report", styles["Title"])
    )

    story.append(Spacer(1, 20))

    if patient:

        # Patient Details
        story.append(
            Paragraph("Patient Details", styles["Heading2"])
        )

        story.append(
            Paragraph(f"Name: {patient[0]}", styles["Normal"])
        )

        story.append(
            Paragraph(f"Age: {patient[1]}", styles["Normal"])
        )

        story.append(
            Paragraph(f"Gender: {patient[2]}", styles["Normal"])
        )

        story.append(
            Paragraph(f"Phone: {patient[3]}", styles["Normal"])
        )

        story.append(
            Paragraph(f"Address: {patient[4]}", styles["Normal"])
        )

        story.append(
            Paragraph(f"Symptoms: {patient[5]}", styles["Normal"])
        )

        story.append(
            Paragraph(
                f"Previous Allergy History: {patient[6] or '-'}",
                styles["Normal"]
            )
        )

        story.append(Spacer(1, 15))

        # AI Analysis
        story.append(
            Paragraph(
                "AI Skin Allergy Analysis",
                styles["Heading2"]
            )
        )

        story.append(
            Paragraph(
                f"Skin Area: {patient[7] or '-'}",
                styles["Normal"]
            )
        )

        story.append(
            Paragraph(
                f"Duration: {patient[8] or '-'}",
                styles["Normal"]
            )
        )

        story.append(
            Paragraph(
                f"Possible Condition: {patient[9] or '-'}",
                styles["Normal"]
            )
        )

        story.append(
            Paragraph(
                f"Basic Guidance: {patient[10] or '-'}",
                styles["Normal"]
            )
        )

        story.append(Spacer(1, 15))

        # Doctor Suggestion
        story.append(
            Paragraph(
                "Doctor Suggestion",
                styles["Heading2"]
            )
        )

        story.append(
            Paragraph(
                f"Suggested Specialist: {patient[11] or '-'}",
                styles["Normal"]
            )
        )

        story.append(
            Paragraph(
                f"Reason: {patient[12] or '-'}",
                styles["Normal"]
            )
        )

        story.append(Spacer(1, 15))

        # Hospital Information
        story.append(
            Paragraph(
                "Hospital Information",
                styles["Heading2"]
            )
        )

        story.append(
            Paragraph(
                f"Location: {patient[13] or '-'}",
                styles["Normal"]
            )
        )

        if patient[14]:

            for hospital in patient[14].split(" | "):

                story.append(
                    Paragraph(
                        f"- {hospital}",
                        styles["Normal"]
                    )
                )

    else:

        story.append(
            Paragraph(
                "No Report Data Available",
                styles["Heading2"]
            )
        )

    story.append(Spacer(1, 20))

    # Warning
    story.append(
        Paragraph(
            "This report is generated for academic/project "
            "demonstration purposes and is not a medical diagnosis. "
            "Please consult a qualified healthcare professional "
            "for proper evaluation.",
            styles["Normal"]
        )
    )

    pdf.build(story)

    buffer.seek(0)

    return buffer.getvalue(), 200, {
        "Content-Type": "application/pdf",
        "Content-Disposition":
            "attachment; filename=skin_allergy_report.pdf"
    }


@app.route("/skin-allergy-info")
def skin_allergy_info():
    return render_template("skin_allergy_info.html")
create_database()

if __name__ == "__main__":
    app.run(debug=True)