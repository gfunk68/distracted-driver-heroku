import os
import shutil
import numpy as np
from flask import Flask, request, jsonify, render_template

import keras
from keras.preprocessing import image
from keras import backend as K
from tensorflow.keras.models import load_model

import cv2

from tensorflow.compat.v1 import ConfigProto
from tensorflow.compat.v1 import InteractiveSession

config = ConfigProto()
config.gpu_options.allow_growth = True
session = InteractiveSession(config=config)

#### Converting Number Codes to Distraction Type ####
# def distractiontype(i):
#     switcher={
#         0:'safe driving',
#         1:'texting right',
#         2:'talking on the phone right',
#         3:'texting left',
#         4:'talking on the phone left',
#         5:'operating the radio',
#         6:'drinking',
#         7:'reaching behind',
#         8:'hair and makeup',
#         9:'talking to passenger'
#     }
#     return switcher.get(i,"Invalid Distraction Method")

#### flask setup ####
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

#### loading a keras model with flask ####
# def loaded_model():
#     global model
#     model = load_model("data/final_model.h5")
 

#### preprocess data function ####
def prepare_image(img):
    #convert image tp numpy array
    img = image.img_to_array(img)
    #scale the image 
    img_data = np.expand_dims(img, 0)
    datagen = image.ImageDataGenerator(rescale=1./255)
    final_data = datagen.flow(img_data)[0]
    return final_data

def getframes(path):
	vidObj = cv2.VideoCapture(path)
	count = 0
	success=1
	images = []

	folder = os.path.join(app.config['UPLOAD_FOLDER'],'video_frames')
	for filename in os.listdir(folder):
		file_path = os.path.join(folder, filename)
		try:
			if os.path.isfile(file_path) or os.path.islink(file_path):
				os.unlink(file_path)
			elif os.path.isdir(file_path):
				shutil.rmtree(file_path)
		except Exception as e:
			print('Failed to delete %s. Reason: %s' % (filepath, e))

	while success:
		success,image = vidObj.read()
		cv2.imwrite(os.path.join('static','uploads','video_frames',"frame%d.jpg" % count),image)
		count += 1

#### flask routes ####
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data")
def data():
    return render_template("data.html")

@app.route("/video", methods=["GET","POST"])
def video():
    data = {"Success": False}
    model = load_model("data/final_model.h5")

    if request.method == "POST":
        if request.files.get("file"):
            # save file to uploads folder
            file = request.files["file"]
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            getframes(filepath)

            images = []
            for filename in os.listdir('static/uploads/video_frames'):
                filepath = os.path.join(app.config['UPLOAD_FOLDER'],'video_frames',filename)
                try:
                    im = image.load_img(filepath,target_size=(480,640))
                except Exception as e:
                    print('Failed to load %s. Reason: %s' % (filename, e))
                img = image.img_to_array(im)
                images.append(img)

            images = np.asarray(images)
            datagen = image.ImageDataGenerator(rescale=1./255)
            video_data = datagen.flow(images)

            predicted_distraction = model.predict_classes(video_data, batch_size=None)
            data["Prediction"]=predicted_distraction.tolist()
            data["Success"]=True

        #return jsonify(data)
    return render_template("video.html",data=data)

@app.route("/model")
def model1():
    return render_template("model.html")

@app.route("/gallery")
def gallery():
    return render_template("gallery.html")

@app.route("/photo", methods=["GET","POST"])
def predict():
    # def loaded_model():
    # global model
    
    model = load_model("data/final_model.h5")

    data = {"Success": False}

    if request.method == "POST":
        if request.files.get("file"):
            # save file to uploads folder
            file = request.files["file"]
            filename = file.filename
                       
            #### make sure image is in correct format and give unique file name
            # if filename.endswith('.jpg'):
            # filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            filepath = f"{app.config['UPLOAD_FOLDER']}/{filename}"
            file.save(filepath)

            # load image in with correct sizing 
            image_size = (480,640)
            im = image.load_img(filepath,target_size=image_size)
            # convert image to an array of values
            image_array = prepare_image(im)

            predicted_distraction = model.predict_classes(image_array)
            predicted_values = model.predict(image_array)
            data["Prediction"]=str(predicted_distraction)
            data["Success"]=True
            data["Values"]=predicted_values.tolist()

            # return jsonify(data)
        return render_template("photo.html",data=data,filename=filename)
    return render_template("photo.html",data=data)

@app.route("/output")
def output():
    return render_template("output.html")

if __name__ == '__main__':
    # loaded_model()
    app.run(debug=True)
