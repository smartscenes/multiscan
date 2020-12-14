import os
from flask import Flask, Response, request, render_template, url_for, redirect

app = Flask(__name__)

@app.route("/test")
def testRoute():
    return Response(status=200)

# @app.route("/upload", methods=['POST'])
# def handleFileUpload():
#     if 'video' in request.files:
#         video = request.files['video']
#         if video.filename != '':
#             video.save(os.path.join('./files', video.filename))
#     return Response(status=201)

# @app.route("/upload", methods=['POST'])
# def handleFileUpload():
#     filename = request.headers.get('filename')
#     data = request.get_data()
#     f = open(os.path.join('./files', filename), 'w+b')
#     f.write(data)
#     f.close()
#     return Response(status=201)

@app.route("/upload", methods=['PUT'])
def handleFileUploadPut():
    filename = request.headers.get('FILE_NAME')
    data = request.get_data()
    f = open(os.path.join('./files', filename), 'w+b')
    f.write(data)
    f.close()
    return Response(status=200)

@app.route("/verify", methods=['GET'])
def verify_file():
    return Response(status=200)

if __name__ == '__main__':
    app.run('0.0.0.0')     