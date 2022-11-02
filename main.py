from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
import secrets,uuid, random, os
import speech_recognition as srecog
from gtts import gTTS
from pydub import AudioSegment
from flask_talisman import Talisman
from waitress import serve
from flask_lt import run_with_lt
from paste.translogger import TransLogger
import time

#DONT FORGET TO CHANGE IN TEST IF YOU CHANGE IP!!!!

import logging
logger = logging.getLogger('waitress')
logger.setLevel(logging.INFO)

r = srecog.Recognizer()

def wav2flac(wav_path):
    flac_path = "%s.flac" % os.path.splitext(wav_path)[0]
    song = AudioSegment.from_wav(wav_path)
    song.export(flac_path, format = "flac")


def convert_to_audio(text):
    x = uuid.uuid1()
    audio = gTTS(text=text, lang='en', tld='com')
    name = f"static/{x}.wav"
    audio.save(name)
    return x

secret = secrets.token_urlsafe(32)

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = secret
Session(app)
run_with_lt(app)

@app.route('/test', methods=['GET'])
def test():
    try:
        os.remove(f"static/{session['name']}.wav")
    except:
        pass
    session['rand'] = random.randint(0,len(session['defs']))
    session['name'] = convert_to_audio(session['defs'][session['rand']])
    print(f"{session['name']} from test")
    try:
        prevterm = f"The answer to the previous question (number {session['counter']}) was: {session['terms'][session['prevrand']]}"
    except:
        prevterm = ''
    print(prevterm)
    return render_template('test.html',content=f"/static/{session['name']}.wav", points=session['points'], sound=session['sound2'], prevans = prevterm,offset=0, hidden1 = session['understood_by_computer'],counter=session['counter'])

@app.route('/test', methods=['GET','POST'])
def test2():
    print(f"{session['name']} from test2")
    if request.method == "POST":
        print('test2, post')
        z = uuid.uuid1()
        file = request.files['file']
        f = open(f"audio/{z}.wav",'wb')
        f.write(file.read())
        f.close()
        os.system(f'ffmpeg -i audio/{z}.wav -acodec pcm_s16le -ac 1 -ar 16000 audio/{z}t.wav')
        os.remove(f"audio/{z}.wav")
        audio = srecog.AudioFile(f"audio/{z}t.wav")
        with audio as source:
            audioData = r.record(source)
        session['understood_by_computer'] = r.recognize_google(audioData)
        print([session['understood_by_computer'].lower()])
        print([session['terms'][session['rand']].lower()])
        print(session['understood_by_computer'].lower())
        if session['understood_by_computer'].lower() == session['terms'][session['rand']].lower().strip():
            session['points'] += 1
            session['sound2'] = 'static/right.mp3'
        else:
            session['points'] -= 1
            session['sound2'] = 'static/wrong.mp3'
        session['prevrand'] = session['rand']
        session['counter'] += 1
        os.remove(f"audio/{z}t.wav")
    return redirect('/test')

@app.route('/', methods=['GET'])
def home2():
    if request.method == 'GET': 
        print('called')
        return render_template('home.html')

@app.route('/', methods=['GET','POST'])
def home():
    session['sound2'] = 0
    session['points'] = 0
    session['test2'] = 'test'
    session['defs'] = []
    session['terms'] = []
    session['counter'] = 0
    session['hidden1'] = 0
    session['understood_by_computer'] = ''
    if request.method == 'POST':
        link = request.form['name']
        z = link.split('_')
        for i in z:
            try:
                i = i.split('~')
                session['defs'].append(i[1])
                session['terms'].append(i[0])
            except IndexError:
                pass
    return redirect('/test')

if __name__ == '__main__':
    serve(TransLogger(app, setup_console_handler=False), host='127.0.0.1', port=5000)