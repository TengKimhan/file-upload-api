import os
import random
from io import BytesIO

import requests
from werkzeug.utils import secure_filename

from app import app, db
from flask import request, jsonify, send_file
from flask_cors import cross_origin
from tika import parser


ALLOWED_EXTENSIONS = set(['pdf', 'png', 'jpg', 'jpeg', 'docx', 'doc', 'json', 'csv', 'xls', 'txt', 'xml', 'ppt', 'pptx'])
UPLOAD_FOLDER = os.path.abspath(os.path.dirname(__file__)) + '/Downloads/'


# create datatable
class Upload(db.Model):
    id = db.Column(db.String(100), primary_key=True)
    filename = db.Column(db.String(50))
    data = db.Column(db.LargeBinary)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def file_type(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower()


@app.route('/file-upload', methods=['POST'])
@cross_origin()
def upload_file():
    file = request.files['file']
    if 'file' not in request.files:
        resp = jsonify({'message': 'No file part in the request'})
        resp.status_code = 400
        return resp
    if file.filename == '':
        resp = jsonify({'message': 'No file selected for uploading'})
        resp.status_code = 400
        return resp
    if file and allowed_file(file.filename):
        filename = file.filename
        target = os.path.join(UPLOAD_FOLDER, filename)
        file.save(target)
        rand_id = random.randint(0, 1000)

        headers = {
            "X-Tika-OCRLanguage": "khm+eng"
        }
        result = parser.from_file(os.path.join(UPLOAD_FOLDER, filename),
                                  requestOptions={'headers': headers, 'timeout': 300},
                                  serverEndpoint="http://172.16.1.176:9998/tika")

        request_solr = [{
            'id': str(rand_id),
            'filePath': os.path.join(UPLOAD_FOLDER, filename),
            'url': str(rand_id),
            'fileType': file_type(filename),
            'fileName': filename,
            'content': result['content']
        }]
        r = requests.post('http://localhost:8983/solr/searchengine/update?commit=true', json=request_solr)

        # insert data to db
        f = open(target, "rb")
        upload = Upload(id=str(rand_id), filename=filename, data=f.read())
        db.session.add(upload)
        db.session.commit()
        f.close()
        return r.json()
    else:
        resp = jsonify({'message': 'Allowed file types are pdf, png, jpg, jpeg, docx'})
        resp.status_code = 400
        return resp


# create download function for download files
@app.route('/download/<upload_id>')
@cross_origin()
def download(upload_id):
    upload = Upload.query.filter_by(id=upload_id).first()
    return send_file(BytesIO(upload.data),
                     download_name=upload.filename, as_attachment=True)


if __name__ == "__main__":
    app.run()
