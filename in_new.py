import os
from flask import Flask
import time
import json
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from pymongo import MongoClient
import certifi
from bson import ObjectId

app = Flask(__name__)

# Load credentials from JSON file
credential = json.load(open('credential.json'))
API_KEY = credential['API_KEY']
ENDPOINT = credential['ENDPOINT']
uri = credential['MONGODB_URI']

# Connect to MongoDB
client = MongoClient(uri, ssl=True, tlsCAFile=certifi.where())
db = client['capstone']
collection = db['Extraction']

# Initialize Computer Vision client
cv_client = ComputerVisionClient(ENDPOINT, CognitiveServicesCredentials(API_KEY))

# Function to extract text from an image
def extract_text_from_image(image_path):
    # Read image file
    with open(image_path, 'rb') as image_file:
        response = cv_client.read_in_stream(image_file, language='en', raw=True)
    
    operationLocation = response.headers['Operation-Location']
    operation_id = operationLocation.split('/')[-1]
    
    # Wait for operation to complete
    time.sleep(5)
    result = cv_client.get_read_result(operation_id)

    # Check if operation succeeded
    if result.status == OperationStatusCodes.succeeded:
        read_results = result.analyze_result.read_results
        extracted_text = ''
        for analyzed_result in read_results:
            for line in analyzed_result.lines:
                extracted_text += line.text + '\n'
        return extracted_text

# Function to process all images in a folder
def process_images_in_folder(folder_path):
    extracted_text = {}
    for filename in os.listdir(folder_path):
        if filename.endswith('.jpg') or filename.endswith('.jpeg') or filename.endswith('.png'):
            image_path = os.path.join(folder_path, filename)
            text = extract_text_from_image(image_path)
            extracted_text[filename] = text
            print(f"Text extracted from {filename}")

    # Insert extracted text into MongoDB with a single ObjectID
    collection.insert_one({'_id': ObjectId(), 'text_data': extracted_text})
    print("Extracted text saved to MongoDB")

if __name__ == '__main__':
    # Specify the folder path containing the images
    folder_path = 'Images'

    # Call the function to process all images in the folder
    process_images_in_folder(folder_path)
