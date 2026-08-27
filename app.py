from flask import Flask, render_template, request, session
import sqlite3

app = Flask(__name__)
app.secret_key = "skin_allergy_secret_key"


def create_database():
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)

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
            return render_template("dashboard.html")

        return "Invalid Email or Password!"

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")
@app.route("/clear-session")
def clear_session():
    session.clear()
    return "Session cleared successfully."


@app.route("/patient-details", methods=["GET", "POST"])
def patient_details():

    if request.method == "POST":

        patient_name = request.form["patient_name"]
        age = request.form["age"]
        gender = request.form["gender"]
        phone = request.form["phone"]
        address = request.form["address"]
        symptoms = request.form["symptoms"]
        allergy_history = request.form["allergy_history"]

        connection = sqlite3.connect("database.db")
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO patients
            (patient_name, age, gender, phone, address, symptoms, allergy_history)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            patient_name,
            age,
            gender,
            phone,
            address,
            symptoms,
            allergy_history
        ))

        connection.commit()
        connection.close()
        session["patient_done"] = True

        return "Patient Details Saved Successfully!"

    return render_template("patient_details.html")
@app.route("/ai-allergy", methods=["GET", "POST"])
def ai_allergy():

    if request.method == "POST":

        skin_area = request.form["skin_area"]
        duration = request.form["duration"]
        symptoms = request.form["symptoms"].lower()
        additional_info = request.form["additional_info"]

        # Simple symptom-based analysis for the academic project
        if "itching" in symptoms and "redness" in symptoms and "rash" in symptoms:
            condition = "Allergic Skin Reaction"
            guidance = "Avoid possible irritants and consult a qualified healthcare professional."

        elif "itching" in symptoms and "dry" in symptoms:
            condition = "Dry or Irritated Skin"
            guidance = "Avoid harsh products and consider consulting a healthcare professional."

        elif "redness" in symptoms and "swelling" in symptoms:
            condition = "Possible Allergic Reaction"
            guidance = "Seek professional medical evaluation, especially if symptoms are severe."

        elif "rash" in symptoms:
            condition = "Possible Skin Irritation"
            guidance = "Avoid suspected irritants and seek professional advice if symptoms continue."

        else:
            condition = "Unclassified Skin Symptoms"
            guidance = "Please consult a qualified healthcare professional for proper evaluation."

        session["skin_area"] = skin_area
        session["duration"] = duration
        session["condition"] = condition
        session["guidance"] = guidance
        session["ai_done"] = True
        return f"""
        <h1>🤖 AI Skin Allergy Analysis</h1>

        <h2>Analysis Result</h2>

        <p><b>Skin Area:</b> {skin_area}</p>
        <p><b>Duration:</b> {duration}</p>
        <p><b>Symptoms:</b> {symptoms}</p>

        <h3>Possible Condition</h3>
        <p>{condition}</p>

        <h3>Basic Guidance</h3>
        <p>{guidance}</p>

        <p>⚠️ This is a project-based preliminary result and
        not a medical diagnosis.</p>

        <a href="/ai-allergy">Analyze Again</a>
        <br>
        <a href="/dashboard">Back to Dashboard</a>
        """

    return render_template("ai_allergy.html")
@app.route("/doctor-suggestion", methods=["GET", "POST"])
def doctor_suggestion():
    if request.method == "POST":

        symptoms = request.form["symptoms"].lower()
        duration = request.form["duration"]

        if "itching" in symptoms and "rash" in symptoms:
            doctor = "Dermatologist"
            reason = "A dermatologist can evaluate skin rashes and itching."

        elif "redness" in symptoms and "swelling" in symptoms:
            doctor = "Dermatologist"
            reason = "A dermatologist can evaluate skin redness and swelling."

        elif "dry" in symptoms:
            doctor = "Dermatologist"
            reason = "A dermatologist can evaluate persistent dry or irritated skin."

        else:
            doctor = "Dermatologist"
            reason = "A dermatologist is the appropriate specialist for skin-related concerns."
            session["doctor_done"] = True
            session["doctor"] = doctor
            session["reason"] = reason

        return f"""
        <h1>👨‍⚕️ Doctor Suggestion</h1>

        <h2>Suggested Specialist</h2>

        <p><b>Doctor Type:</b> {doctor}</p>

        <p><b>Reason:</b> {reason}</p>

        <p><b>Duration:</b> {duration}</p>

        <p>
        ⚠️ This is a project-based suggestion and not a medical diagnosis.
        Please consult a qualified healthcare professional.
        </p>

        <a href="/doctor-suggestion">Check Again</a>
        <br>
        <a href="/dashboard">Back to Dashboard</a>
        """

    return render_template("doctor_suggestion.html")
@app.route("/hospital-location", methods=["GET", "POST"])
def hospital_location():

    if request.method == "POST":

        location = request.form.get("location", "").strip().lower()

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
                "Government Rajaji Hospital, Madurai - Dermatology Department / Contact Dermatitis Clinic",
                "AIIMS Madurai - Department of Dermatology",
                "Vadamalayan Hospitals, Madurai - Dermatology / Skin Allergy Care",
                "Gem Skin, Hair and Laser Centre, Madurai - Skin Care / Dermatology"
            ]

        else:
            hospitals = [
                "No hospital information available for this location in the demo."
            ]

        hospital_list = ""

        for hospital in hospitals:
            hospital_list += f"<li>{hospital}</li>"
            session["hospital_done"] = True
            session["hospital_location"] = location.title()
            session["hospitals"] = hospitals

        return f"""
        <h1>🏥 Hospital Information</h1>

        <h2>Location: {location.title()}</h2>

        <h3>Available Hospitals</h3>

        <ul>
            {hospital_list}
        </ul>

        <p>
        ⚠️ This hospital information is for project demonstration purposes.
        Please verify hospital details before visiting.
        </p>

        <a href="/hospital-location">Search Again</a>
        <br>
        <a href="/dashboard">Back to Dashboard</a>
        """

    return render_template("hospital_location.html")
    
@app.route("/report")
def report():

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    patient = None

    if session.get("patient_done"):
        cursor.execute("""
            SELECT patient_name, age, gender, phone, address, symptoms, allergy_history
            FROM patients
            ORDER BY rowid DESC
            LIMIT 1
        """)

        patient = cursor.fetchone()

    connection.close()

    if patient:
        patient_name = patient[0]
        age = patient[1]
        gender = patient[2]
        phone = patient[3]
        address = patient[4]
        symptoms = patient[5]
        allergy_history = patient[6]
    else:
        patient_name = "-"
        age = "-"
        gender = "-"
        phone = "-"
        address = "-"
        symptoms = "-"
        allergy_history = "-"

    return render_template(
        "report.html",

        patient_done=session.get("patient_done", False),

        ai_done=session.get("ai_done", False),
        skin_area=session.get("skin_area", "-"),
        duration=session.get("duration", "-"),
        condition=session.get("condition", "-"),
        guidance=session.get(
            "guidance",
            "Please consult a qualified dermatologist."
        ),

        doctor_done=session.get("doctor_done", False),
        doctor=session.get("doctor", "-"),
        reason=session.get("reason", "-"),

        hospital_done=session.get("hospital_done", False),
        location=session.get("hospital_location", "-"),
        hospitals=session.get("hospitals", []),

        patient_name=patient_name,
        age=age,
        gender=gender,
        phone=phone,
        address=address,
        symptoms=symptoms,
        allergy_history=allergy_history
    )
if __name__ == "__main__":
    create_database()
    app.run(debug=True)