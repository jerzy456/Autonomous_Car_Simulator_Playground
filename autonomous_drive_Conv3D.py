import socketio
import eventlet
import numpy as np
from flask import Flask
from keras.models import load_model
import base64
from io import BytesIO
from PIL import Image
import cv2
from collections import deque

#create server for bidirectional communication server to dispatch traffic to simulator
sio = socketio.Server()

#create instance of flask applacation in app class
app = Flask(__name__)  # '__main__'
speed_limit = 100

BUFFER_SIZE = 15

image_buffer =deque()

def img_preprocess(img):
    img = img[60:135, :, :]
    img = cv2.cvtColor(img, cv2.COLOR_RGB2YUV)
    img = cv2.GaussianBlur(img, (3, 3), 0)
    img = cv2.resize(img, (200, 66))
    img = img / 255
    return img


@sio.on('telemetry')
def telemetry(sid, data):
    speed =  float(data['speed'])
    image = Image.open(BytesIO(base64.b64decode(data['image'])))
    image = np.asarray(image)
    image = img_preprocess(image)
    image = np.array([image])
    image_buffer.appendleft(image)
    steering_angle=0.0


    if len(image_buffer)>=BUFFER_SIZE:

        ThreeD_frame=np.asarray(image_buffer)
        steering_angle = float(model.predict(ThreeD_frame))
        image_buffer.pop()

    throttle = 1.0 - speed / speed_limit
    print('{} {} {} {} '.format(steering_angle, throttle, speed,len(image_buffer)))
    send_control(steering_angle, throttle)


#on message connection
@sio.on('connect')
def connect(sid, environ):
    print('Connected')
    send_control(0, 1)


def send_control(steering_angle, throttle):
    sio.emit('steer', data={
        'steering_angle': steering_angle.__str__(),
        'throttle': throttle.__str__()
    })

@app.route('/home')
def greeting():
    return 'App is running!'

if __name__ == '__main__':
    model = load_model('RNN_model-12-0.04.hdf5')

    app = socketio.Middleware(sio, app)
    eventlet.wsgi.server(eventlet.listen(('', 4567)), app)