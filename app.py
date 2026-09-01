from flask import Flask, render_template, request, redirect,session
import mysql.connector
import os
from pypdf import PdfReader
from dotenv import load_dotenv
from groq import Groq
app=Flask(__name__)
app.secret_key = "assistant123"
load_dotenv()

cli = Groq(api_key=os.getenv("GROQ_API_KEY"))

dbase=mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="aisummarizer"
)
com=dbase.cursor()
@app.route("/home")
def home():
    return render_template("home.html")
@app.route("/")
def login_page():
    return render_template("login.html")
@app.route("/dashboard")
def dashboard():
    username = session.get("username")
    email = session.get("email")
    return render_template("dashboard.html",username=username,email=email)
@app.route("/quiz", methods=["POST","GET"])
def quiz():
    if request.method == "POST":
        file = request.files["study_file"]
        if file.filename=="":
                return "file not selected"
        print(file.filename)
        name, extension=os.path.splitext(file.filename)
        allowed=[".pdf"]
        if extension.lower() not in allowed:
            return"file type not accepted"
        os.makedirs("quiz",exist_ok=True)
        file.save("quiz/"+ file.filename)
        reader=PdfReader("quiz/"+file.filename)
        text="" 
        for page in reader.pages:
            text+=page.extract_text()+"\n"

        response = cli.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "user",
                    "content": f"""
                    Create a quiz from the following study material.

                    Generate 5 multiple-choice questions.
                    Each question must have 4 options.

                    Use exactly this format:

                    1. Question text
                    a) Option A
                    b) Option B
                    c) Option C
                    d) Option D

                    2. Question text
                    a) Option A
                    b) Option B
                    c) Option C
                    d) Option D

                    3. Question text
                    a) Option A
                    b) Option B
                    c) Option C
                    d) Option D

                    4. Question text
                    a) Option A
                    b) Option B
                    c) Option C
                    d) Option D

                    5. Question text
                    a) Option A
                    b) Option B
                    c) Option C
                    d) Option D

                    At the end, write:

                    Answers:
                    1. a
                    2. b
                    3. c
                    4. d
                    5. a

                    IMPORTANT:
                    - Only write the letter a, b, c, or d for each answer.
                    - Do not write "Correct answer:"
                    - Do not write the option text in the Answers section.
                    - Do not add explanations.
                    - Do not add extra questions.

                    Study material:
                    {text}
                    """
                }
            ]
        )

        quiz_text = response.choices[0].message.content

        return render_template("quiz.html", quiz=quiz_text)
    return render_template("quiz.html")

@app.route("/upload", methods=["POST","GET"])
def upload():
    if request.method == "POST":
        file = request.files["study_file"]
        if file.filename=="":
                return "file not selected"
        print(file.filename)
        name, extension=os.path.splitext(file.filename)
        allowed=[".pdf"]
        if extension.lower() not in allowed:
            return"file type not accepted"
        os.makedirs("upload",exist_ok=True)
        file.save("upload/"+ file.filename)
        reader=PdfReader("upload/"+file.filename)
        text="" 
        for page in reader.pages:
            text+=page.extract_text()+"\n"
        response= cli.chat.completions.create(
                            model="openai/gpt-oss-20b",
                            messages=[
                                {
                                    "role": "user",
                                    "content": f"""
                                    Create a summary from the following study material.
                
                                highlight important points bold the headings and sun headings
                                dont use symbols like #
                                the things you are adding * to dont add ** just bold it and underline.
                                summary should be able to help in quick revision of the study material
                                it should be long enough for a 5 marks question
                                key points should be given in bullet points
                
                                    Study material:
                                    {text}
                                    """
                                }
                            ]
                        )
        summary_text = response.choices[0].message.content
        
        com.execute("INSERT INTO history (UserID, summary) VALUES (%s, %s)", (session["user_id"], summary_text))
        dbase.commit()

        return render_template("summary.html",text=summary_text)

    return render_template("upload.html")


@app.route("/summary")
def summary():
    
    return render_template("summary.html")

@app.route("/login", methods=["POST"])
def login():
    username= request.form["uname"]
    password= request.form["pass"]
    print(username)
    print(password)
    com.execute("SELECT Username, Email,UserID FROM signup WHERE Username=%s AND Password=%s",(username,password))
    user=com.fetchone()
    if user:
        session["username"] = user[0]  
        session["email"] = user[1]
        session["user_id"] = user[2]
        return redirect("/home")
    return "Invalid username or password"
@app.route("/signup",methods=["POST","GET"])
def signup():
    if request.method == "POST":
        fname=request.form["fname"]
        lname=request.form["lname"]
        uname=request.form["uname"]
        password=request.form["pass"]
        email=request.form["email"]
        language=request.form["lang"]
        print(fname)
        print(lname)
        print(uname)
        print(email)
        print(password)
        print(language)
        com.execute(
            "INSERT into signup(FirstName,LastName," \
            "Username,Email,Password,Language) VALUES(%s,%s,%s,%s,%s,%s)",
            (fname,lname, uname, email, password, language)
        )
        dbase.commit()
        return redirect("/")
    return render_template("signup.html")
if __name__ == "__main__":
    app.run(debug=True)