from flask import Flask, request, jsonify,send_file,render_template
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import certifi
import os
import io
import json
import requests
from nlp_module import compare_and_extract_keywords
from in_new import extract_text_and_save_to_mongodb
from pdf_handler import get_pdf_path,read_pdf_content


app = Flask(__name__)
credential = json.load(open('credential.json'))
uri = credential['MONGODB_URI']
# Initialize PyMongo with the Flask app
client = MongoClient(uri,ssl=True,tlsCAFile=certifi.where())
db = client['capstone']


# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
CORS(app)


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')

    # Here, you would typically check the credentials against a database
    # For simplicity, let's assume the credentials are hardcoded
    if role == 'Administrator':
        if username == 'admin' and password == 'admin':
            return jsonify({'message': 'Login successful'})
        else:
            return jsonify({'message': 'Invalid credentials'}), 401
    elif role == 'Faculty':
        if username == 'faculty' and password == 'faculty':
            return jsonify({'message': 'Login successful'})
        else:
            return jsonify({'message': 'Invalid credentials'}), 401
    else:
        return jsonify({'message': 'Invalid role'}), 400

@app.route('/admin/api/examinations', methods=['GET'])
def get_examinations():
    examinations = list(db.examinations.find())
    return jsonify(examinations)

@app.route('/admin/api/departments/<exam_id>', methods=['GET'])
def get_departments(exam_id):
    exam_id = exam_id.strip() 
    departments = list(db.departments.find({'examId': (exam_id)}))
    return jsonify(departments)

@app.route('/admin/api/courses/<dept_id>', methods=['GET'])
def get_courses( dept_id):
    # Assuming you have a way to map departments to exams, possibly through a mapping collection
    # or by embedding department IDs within exam documents.
    dept_id=dept_id.strip()
    courses = list(db.courses.find({'departmentId': dept_id}))
    return jsonify(courses)

@app.route('/admin/api/exams/<exam_id>/departments/<dept_id>/courses/<course_id>/answer_scripts', methods=['GET'])
def get_answer_scripts_for_course(exam_id, dept_id, course_id):
    answer_scripts = list(db.answer_scripts.find({'courseId': course_id}))
    return jsonify(answer_scripts)

@app.route('/admin/api/get_pdf/<path:filename>', methods=['GET'])
def get_pdf(filename):
    folder_name = '3rd Semester Exams, May 2022-1BM20 Batch/ISE/DBMS'  # You can adjust this path according to your directory structure
    pdf_path = get_pdf_path(folder_name, filename)
    
    if not os.path.isfile(pdf_path):
        return jsonify({'message': 'PDF not found'}), 404

    pdf_content = read_pdf_content(pdf_path)
    
    return send_file(
        io.BytesIO(pdf_content),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )
#Please add question number AN IMPORTANT FIELD which must be added its a game changer for us

def perform_nlp_analysis(paragraph1, paragraph2):
    result = compare_and_extract_keywords(paragraph1, paragraph2)
    return result

@app.route('/admin/api/performnlp', methods=['POST'])
def analyze_text_similarity():
    try:
        data = request.get_json()
        paragraph1 = data.get('paragraph1')
        paragraph2 = data.get('paragraph2')

        if not paragraph1 or not paragraph2:
            return jsonify({'error': 'Please provide both paragraphs for analysis.'}), 400

        result = compare_and_extract_keywords(paragraph1, paragraph2)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': 'An error occurred while processing the request.', 'details': str(e)}), 500


@app.route('/admin/api/exams/performocr', methods=['GET', 'POST'])
def perform_ocr():
    if request.method == 'POST':
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file is an image
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        if file:
            # Save file to server
            image_path = 'uploaded_image.jpg'
            file.save(image_path)
            
            # Extract text and save to MongoDB
            extract_text_and_save_to_mongodb(image_path)
            
            return jsonify({'message': 'Text extracted and saved to MongoDB successfully'}), 200
        else:
            return jsonify({'error': 'Unsupported file format'}), 400
    else:
        return render_template('upload.html')


