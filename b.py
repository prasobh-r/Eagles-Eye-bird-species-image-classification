from PIL import Image
from tensorflow.keras.preprocessing.image import load_img, img_to_array
import numpy as np
import pandas as pd
import textwrap
import tensorflow
from matplotlib import pyplot as plt
from tensorflow import expand_dims
from keras.models import load_model
import google.generativeai as palm
from flask import Flask, render_template, url_for, redirect,request,flash,session,send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError, Email
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import os
from details import bdetails
from bdapi import birdofday
import json
from bmap import bmap




app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'thisisasecretkey'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

palm.configure(api_key="AIzaSyAqJ8w5cn-Rq2LlzONPhVY6Z7e73iAYjO8")


UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)


class RegisterForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                'That username already exists. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')

class feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(40), nullable=False)
    message = db.Column(db.String(500), nullable=False)

class feedbackForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired(), Length(max=20)])
    subject = StringField('Subject', validators=[InputRequired(), Length(max=100)])
    email = StringField('Email', validators=[InputRequired(), Email(), Length(max=40)])
    message = StringField('Message', validators=[InputRequired(), Length(max=500)])
    submit = SubmitField('Submit')

with app.app_context():
    db.create_all()


@app.route('/')
def home():  
    with open('birdofday.json', 'r+') as file:
            data = json.load(file)
            commonname = data['cname']
            bdes = data['des']
    return render_template('home.html',cname=commonname,des=bdes)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.username.data=='admin' and form.password.data=='admin123':
            session['admin']=True
        else:
            session['admin']=False
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                session['logged_in'] = True
                print(session['admin'])
                next_url =  session.get('previous_page', url_for('home'))
                print(next_url)
                if request.referrer:
                    print("Referrer:", request.referrer)
                return redirect(next_url)
            else:
                flash('Invalid username or password', 'error')
        else:
            flash('Please check your input', 'error')
    return render_template('login.html', form=form)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    session['admin']=False
    logout_user()
    session.pop('logged_in', None)
    return redirect(url_for('home'))

@ app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)



@app.route('/predict', methods=['GET','POST'])
def predict():
    if not current_user.is_authenticated:
        session['previous_page'] = request.url
        return redirect(url_for('login'))
    return render_template('predict.html')
    
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'image' not in request.files:
        return redirect(request.url)
    file = request.files['image']
    if file.filename == '':
        return redirect(request.url)
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return processed_img(filename)        

def processed_img(img_name):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], img_name)
    img = load_img(file_path, target_size=(224, 224, 3))
    img_array = img_to_array(img)
    img_array = np.expand_dims(img_array, 0)
    predictions = model.predict(img_array)
    class_labels = lab 
    score = tensorflow.nn.softmax(predictions[0])
    res = f"{class_labels[np.argmax(score)]}"
    top_3_indices = sorted(predictions.argsort()[0][-3:][::-1])
    values = predictions[0][top_3_indices] * 100
    labels = [class_labels[i] for i in top_3_indices]
    l = []
    for x in labels:
        wrapped_text = '\n'.join(x.split(' '))
        l.append(wrapped_text)
    prediction_df = pd.DataFrame({
        "Common Name": l,
        "Probability": values,
    })
    prediction_df =prediction_df.sort_values("Probability", ascending=True)
    session['predictions'] = prediction_df.to_json(orient='records')
    display = palm.generate_text(prompt="short description about " + res + " bird in 250 words")
    generated_text = display.candidates[0]['output']  
    plot_path = generate_plot(prediction_df, img_name)  
    return redirect(url_for('result', result=res, des=generated_text, img=img_name, plot=plot_path))

def generate_plot(predictions_df, img_name):
    fig, ax = plt.subplots(figsize=(25, 12))
    ax.barh(predictions_df['Common Name'], predictions_df['Probability'], height=0.3)
    for s in ['top', 'bottom', 'left', 'right']:
        ax.spines[s].set_visible(False)
    ax.xaxis.set_ticks_position('none')
    ax.yaxis.set_ticks_position('none')
    ax.xaxis.set_tick_params(pad=5)
    ax.yaxis.set_tick_params(pad=10)
    ax.xaxis.set_tick_params(labelsize=15)
    ax.yaxis.set_tick_params(labelsize=25)

    ax.grid(True, color='grey', linestyle='-.', linewidth=0.5, alpha=0.2)
    for i in ax.patches:
        plt.text(i.get_width()+5, i.get_y()+ i.get_height()/2, str(round(i.get_width(), 2)), fontsize=25, fontweight='bold', color='black', ha='center', va='center')
    img_name = "top_predictions" 
    plot_filename = f"{img_name}_plot.png"
    plot_path = os.path.join(app.config['UPLOAD_FOLDER'], plot_filename)
    fig.savefig(plot_path)
    plt.clf()
    return plot_filename


@app.route('/result/<result>/<des>/<img>/<plot>')
def result(result, des, img, plot):
    predictions_json = session.get('predictions', '[]')
    predictions_df = pd.read_json(predictions_json, orient='records')
    x = bdetails(result)
    bmap(result)
    return render_template('c.html', result=result, des=des, img=img, plot=plot, predictions=predictions_df.to_dict(orient='records'), det=x)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
@login_required
def contact():
    form = feedbackForm()
    if form.submit.data == True:
        print(form.name.data)
        new_feedback = feedback(
            name=form.name.data,
            subject=form.subject.data,
            email=form.email.data,
            message=form.message.data
        )
        db.session.add(new_feedback)
        db.session.commit()
        return redirect(url_for('home')) 
    return render_template('contact.html', form=form)

@app.route('/view_feedbacks')
@login_required
def view_feedbacks():
    print(session['admin'])
    if session['admin']==True:
        feedbacks = feedback.query.all() 
        return render_template('viewfeedbacks.html', feedbacks=feedbacks)
    else:
        return redirect(url_for('home'))

model = load_model('b.h5', compile=False)


lab = {0: 'ABBOTTS BABBLER',
 1: 'ABBOTTS BOOBY',
 2: 'ABYSSINIAN GROUND HORNBILL',
 3: 'AFRICAN CROWNED CRANE',
 4: 'AFRICAN EMERALD CUCKOO',
 5: 'AFRICAN FIREFINCH',
 6: 'AFRICAN OYSTER CATCHER',
 7: 'AFRICAN PIED HORNBILL',
 8: 'AFRICAN PYGMY GOOSE',
 9: 'ALBATROSS',
 10: 'ALBERTS TOWHEE',
 11: 'ALEXANDRINE PARAKEET',
 12: 'ALPINE CHOUGH',
 13: 'ALTAMIRA YELLOWTHROAT',
 14: 'AMERICAN AVOCET',
 15: 'AMERICAN BITTERN',
 16: 'AMERICAN COOT',
 17: 'AMERICAN DIPPER',
 18: 'AMERICAN FLAMINGO',
 19: 'AMERICAN GOLDFINCH',
 20: 'AMERICAN KESTREL',
 21: 'AMERICAN PIPIT',
 22: 'AMERICAN REDSTART',
 23: 'AMERICAN ROBIN',
 24: 'AMERICAN WIGEON',
 25: 'AMETHYST WOODSTAR',
 26: 'ANDEAN GOOSE',
 27: 'ANDEAN LAPWING',
 28: 'ANDEAN SISKIN',
 29: 'ANHINGA',
 30: 'ANIANIAU',
 31: 'ANNAS HUMMINGBIRD',
 32: 'ANTBIRD',
 33: 'ANTILLEAN EUPHONIA',
 34: 'APAPANE',
 35: 'APOSTLEBIRD',
 36: 'ARARIPE MANAKIN',
 37: 'ASHY STORM PETREL',
 38: 'ASHY THRUSHBIRD',
 39: 'ASIAN CRESTED IBIS',
 40: 'ASIAN DOLLARD BIRD',
 41: 'ASIAN GREEN BEE EATER',
 42: 'ASIAN OPENBILL STORK',
 43: 'AUCKLAND SHAQ',
 44: 'AUSTRAL CANASTERO',
 45: 'AUSTRALASIAN FIGBIRD',
 46: 'AVADAVAT',
 47: 'AZARAS SPINETAIL',
 48: 'AZURE BREASTED PITTA',
 49: 'AZURE JAY',
 50: 'AZURE TANAGER',
 51: 'AZURE TIT',
 52: 'BAIKAL TEAL',
 53: 'BALD EAGLE',
 54: 'BALD IBIS',
 55: 'BALI STARLING',
 56: 'BALTIMORE ORIOLE',
 57: 'BANANAQUIT',
 58: 'BAND TAILED GUAN',
 59: 'BANDED BROADBILL',
 60: 'BANDED PITA',
 61: 'BANDED STILT',
 62: 'BAR-TAILED GODWIT',
 63: 'BARN OWL',
 64: 'BARN SWALLOW',
 65: 'BARRED PUFFBIRD',
 66: 'BARROWS GOLDENEYE',
 67: 'BAY-BREASTED WARBLER',
 68: 'BEARDED BARBET',
 69: 'BEARDED BELLBIRD',
 70: 'BEARDED REEDLING',
 71: 'BELTED KINGFISHER',
 72: 'BIRD OF PARADISE',
 73: 'BLACK AND YELLOW BROADBILL',
 74: 'BLACK BAZA',
 75: 'BLACK BREASTED PUFFBIRD',
 76: 'BLACK COCKATO',
 77: 'BLACK FACED SPOONBILL',
 78: 'BLACK FRANCOLIN',
 79: 'BLACK HEADED CAIQUE',
 80: 'BLACK NECKED STILT',
 81: 'BLACK SKIMMER',
 82: 'BLACK SWAN',
 83: 'BLACK TAIL CRAKE',
 84: 'BLACK THROATED BUSHTIT',
 85: 'BLACK THROATED HUET',
 86: 'BLACK THROATED WARBLER',
 87: 'BLACK VENTED SHEARWATER',
 88: 'BLACK VULTURE',
 89: 'BLACK-CAPPED CHICKADEE',
 90: 'BLACK-NECKED GREBE',
 91: 'BLACK-THROATED SPARROW',
 92: 'BLACKBURNIAM WARBLER',
 93: 'BLONDE CRESTED WOODPECKER',
 94: 'BLOOD PHEASANT',
 95: 'BLUE COAU',
 96: 'BLUE DACNIS',
 97: 'BLUE GRAY GNATCATCHER',
 98: 'BLUE GROSBEAK',
 99: 'BLUE GROUSE',
 100: 'BLUE HERON',
 101: 'BLUE MALKOHA',
 102: 'BLUE THROATED PIPING GUAN',
 103: 'BLUE THROATED TOUCANET',
 104: 'BOBOLINK',
 105: 'BORNEAN BRISTLEHEAD',
 106: 'BORNEAN LEAFBIRD',
 107: 'BORNEAN PHEASANT',
 108: 'BRANDT CORMARANT',
 109: 'BREWERS BLACKBIRD',
 110: 'BROWN CREPPER',
 111: 'BROWN HEADED COWBIRD',
 112: 'BROWN NOODY',
 113: 'BROWN THRASHER',
 114: 'BUFFLEHEAD',
 115: 'BULWERS PHEASANT',
 116: 'BURCHELLS COURSER',
 117: 'BUSH TURKEY',
 118: 'CAATINGA CACHOLOTE',
 119: 'CABOTS TRAGOPAN',
 120: 'CACTUS WREN',
 121: 'CALIFORNIA CONDOR',
 122: 'CALIFORNIA GULL',
 123: 'CALIFORNIA QUAIL',
 124: 'CAMPO FLICKER',
 125: 'CANARY',
 126: 'CANVASBACK',
 127: 'CAPE GLOSSY STARLING',
 128: 'CAPE LONGCLAW',
 129: 'CAPE MAY WARBLER',
 130: 'CAPE ROCK THRUSH',
 131: 'CAPPED HERON',
 132: 'CAPUCHINBIRD',
 133: 'CARMINE BEE-EATER',
 134: 'CASPIAN TERN',
 135: 'CASSOWARY',
 136: 'CEDAR WAXWING',
 137: 'CERULEAN WARBLER',
 138: 'CHARA DE COLLAR',
 139: 'CHATTERING LORY',
 140: 'CHESTNET BELLIED EUPHONIA',
 141: 'CHESTNUT WINGED CUCKOO',
 142: 'CHINESE BAMBOO PARTRIDGE',
 143: 'CHINESE POND HERON',
 144: 'CHIPPING SPARROW',
 145: 'CHUCAO TAPACULO',
 146: 'CHUKAR PARTRIDGE',
 147: 'CINNAMON ATTILA',
 148: 'CINNAMON FLYCATCHER',
 149: 'CINNAMON TEAL',
 150: 'CLARKS GREBE',
 151: 'CLARKS NUTCRACKER',
 152: 'COCK OF THE  ROCK',
 153: 'COCKATOO',
 154: 'COLLARED ARACARI',
 155: 'COLLARED CRESCENTCHEST',
 156: 'COMMON FIRECREST',
 157: 'COMMON GRACKLE',
 158: 'COMMON HOUSE MARTIN',
 159: 'COMMON IORA',
 160: 'COMMON LOON',
 161: 'COMMON POORWILL',
 162: 'COMMON STARLING',
 163: 'COPPERSMITH BARBET',
 164: 'COPPERY TAILED COUCAL',
 165: 'CRAB PLOVER',
 166: 'CRANE HAWK',
 167: 'CREAM COLORED WOODPECKER',
 168: 'CRESTED AUKLET',
 169: 'CRESTED CARACARA',
 170: 'CRESTED COUA',
 171: 'CRESTED FIREBACK',
 172: 'CRESTED KINGFISHER',
 173: 'CRESTED NUTHATCH',
 174: 'CRESTED OROPENDOLA',
 175: 'CRESTED SERPENT EAGLE',
 176: 'CRESTED SHRIKETIT',
 177: 'CRESTED WOOD PARTRIDGE',
 178: 'CRIMSON CHAT',
 179: 'CRIMSON SUNBIRD',
 180: 'CROW',
 181: 'CUBAN TODY',
 182: 'CUBAN TROGON',
 183: 'CURL CRESTED ARACURI',
 184: 'D-ARNAUDS BARBET',
 185: 'DALMATIAN PELICAN',
 186: 'DARJEELING WOODPECKER',
 187: 'DARK EYED JUNCO',
 188: 'DAURIAN REDSTART',
 189: 'DEMOISELLE CRANE',
 190: 'DOUBLE BARRED FINCH',
 191: 'DOUBLE BRESTED CORMARANT',
 192: 'DOUBLE EYED FIG PARROT',
 193: 'DOWNY WOODPECKER',
 194: 'DUNLIN',
 195: 'DUSKY LORY',
 196: 'DUSKY ROBIN',
 197: 'EARED PITA',
 198: 'EASTERN BLUEBIRD',
 199: 'EASTERN BLUEBONNET',
 200: 'EASTERN GOLDEN WEAVER',
 201: 'EASTERN MEADOWLARK',
 202: 'EASTERN ROSELLA',
 203: 'EASTERN TOWEE',
 204: 'EASTERN WIP POOR WILL',
 205: 'EASTERN YELLOW ROBIN',
 206: 'ECUADORIAN HILLSTAR',
 207: 'EGYPTIAN GOOSE',
 208: 'ELEGANT TROGON',
 209: 'ELLIOTS  PHEASANT',
 210: 'EMERALD TANAGER',
 211: 'EMPEROR PENGUIN',
 212: 'EMU',
 213: 'ENGGANO MYNA',
 214: 'EURASIAN BULLFINCH',
 215: 'EURASIAN GOLDEN ORIOLE',
 216: 'EURASIAN MAGPIE',
 217: 'EUROPEAN GOLDFINCH',
 218: 'EUROPEAN TURTLE DOVE',
 219: 'EVENING GROSBEAK',
 220: 'FAIRY BLUEBIRD',
 221: 'FAIRY PENGUIN',
 222: 'FAIRY TERN',
 223: 'FAN TAILED WIDOW',
 224: 'FASCIATED WREN',
 225: 'FIERY MINIVET',
 226: 'FIORDLAND PENGUIN',
 227: 'FIRE TAILLED MYZORNIS',
 228: 'FLAME BOWERBIRD',
 229: 'FLAME TANAGER',
 230: 'FOREST WAGTAIL',
 231: 'FRIGATE',
 232: 'FRILL BACK PIGEON',
 233: 'GAMBELS QUAIL',
 234: 'GANG GANG COCKATOO',
 235: 'GILA WOODPECKER',
 236: 'GILDED FLICKER',
 237: 'GLOSSY IBIS',
 238: 'GO AWAY BIRD',
 239: 'GOLD WING WARBLER',
 240: 'GOLDEN BOWER BIRD',
 241: 'GOLDEN CHEEKED WARBLER',
 242: 'GOLDEN CHLOROPHONIA',
 243: 'GOLDEN EAGLE',
 244: 'GOLDEN PARAKEET',
 245: 'GOLDEN PHEASANT',
 246: 'GOLDEN PIPIT',
 247: 'GOULDIAN FINCH',
 248: 'GRANDALA',
 249: 'GRAY CATBIRD',
 250: 'GRAY KINGBIRD',
 251: 'GRAY PARTRIDGE',
 252: 'GREAT ARGUS',
 253: 'GREAT GRAY OWL',
 254: 'GREAT JACAMAR',
 255: 'GREAT KISKADEE',
 256: 'GREAT POTOO',
 257: 'GREAT TINAMOU',
 258: 'GREAT XENOPS',
 259: 'GREATER PEWEE',
 260: 'GREATER PRAIRIE CHICKEN',
 261: 'GREATOR SAGE GROUSE',
 262: 'GREEN BROADBILL',
 263: 'GREEN JAY',
 264: 'GREEN MAGPIE',
 265: 'GREEN WINGED DOVE',
 266: 'GREY CUCKOOSHRIKE',
 267: 'GREY HEADED CHACHALACA',
 268: 'GREY HEADED FISH EAGLE',
 269: 'GREY PLOVER',
 270: 'GROVED BILLED ANI',
 271: 'GUINEA TURACO',
 272: 'GUINEAFOWL',
 273: 'GURNEYS PITTA',
 274: 'GYRFALCON',
 275: 'HAMERKOP',
 276: 'HARLEQUIN DUCK',
 277: 'HARLEQUIN QUAIL',
 278: 'HARPY EAGLE',
 279: 'HAWAIIAN GOOSE',
 280: 'HAWFINCH',
 281: 'HELMET VANGA',
 282: 'HEPATIC TANAGER',
 283: 'HIMALAYAN BLUETAIL',
 284: 'HIMALAYAN MONAL',
 285: 'HOATZIN',
 286: 'HOODED MERGANSER',
 287: 'HOOPOES',
 288: 'HORNED GUAN',
 289: 'HORNED LARK',
 290: 'HORNED SUNGEM',
 291: 'HOUSE FINCH',
 292: 'HOUSE SPARROW',
 293: 'HYACINTH MACAW',
 294: 'IBERIAN MAGPIE',
 295: 'IBISBILL',
 296: 'IMPERIAL SHAQ',
 297: 'INCA TERN',
 298: 'INDIAN BUSTARD',
 299: 'INDIAN PITTA',
 300: 'INDIAN ROLLER',
 301: 'INDIAN VULTURE',
 302: 'INDIGO BUNTING',
 303: 'INDIGO FLYCATCHER',
 304: 'INLAND DOTTEREL',
 305: 'IVORY BILLED ARACARI',
 306: 'IVORY GULL',
 307: 'IWI',
 308: 'JABIRU',
 309: 'JACK SNIPE',
 310: 'JACOBIN PIGEON',
 311: 'JANDAYA PARAKEET',
 312: 'JAPANESE ROBIN',
 313: 'JAVA SPARROW',
 314: 'JOCOTOCO ANTPITTA',
 315: 'KAGU',
 316: 'KAKAPO',
 317: 'KILLDEAR',
 318: 'KING EIDER',
 319: 'KING VULTURE',
 320: 'KIWI',
 321: 'KNOB BILLED DUCK',
 322: 'KOOKABURRA',
 323: 'LARK BUNTING',
 324: 'LAUGHING GULL',
 325: 'LAZULI BUNTING',
 326: 'LESSER ADJUTANT',
 327: 'LILAC ROLLER',
 328: 'LIMPKIN',
 329: 'LITTLE AUK',
 330: 'LOGGERHEAD SHRIKE',
 331: 'LONG-EARED OWL',
 332: 'LOONEY BIRDS',
 333: 'LUCIFER HUMMINGBIRD',
 334: 'MAGPIE GOOSE',
 335: 'MALABAR HORNBILL',
 336: 'MALACHITE KINGFISHER',
 337: 'MALAGASY WHITE EYE',
 338: 'MALEO',
 339: 'MALLARD DUCK',
 340: 'MANDRIN DUCK',
 341: 'MANGROVE CUCKOO',
 342: 'MARABOU STORK',
 343: 'MASKED BOBWHITE',
 344: 'MASKED BOOBY',
 345: 'MASKED LAPWING',
 346: 'MCKAYS BUNTING',
 347: 'MERLIN',
 348: 'MIKADO  PHEASANT',
 349: 'MILITARY MACAW',
 350: 'MOURNING DOVE',
 351: 'MYNA',
 352: 'NICOBAR PIGEON',
 353: 'NOISY FRIARBIRD',
 354: 'NORTHERN BEARDLESS TYRANNULET',
 355: 'NORTHERN CARDINAL',
 356: 'NORTHERN FLICKER',
 357: 'NORTHERN FULMAR',
 358: 'NORTHERN GANNET',
 359: 'NORTHERN GOSHAWK',
 360: 'NORTHERN JACANA',
 361: 'NORTHERN MOCKINGBIRD',
 362: 'NORTHERN PARULA',
 363: 'NORTHERN RED BISHOP',
 364: 'NORTHERN SHOVELER',
 365: 'OCELLATED TURKEY',
 366: 'OILBIRD',
 367: 'OKINAWA RAIL',
 368: 'ORANGE BREASTED TROGON',
 369: 'ORANGE BRESTED BUNTING',
 370: 'ORIENTAL BAY OWL',
 371: 'ORNATE HAWK EAGLE',
 372: 'OSPREY',
 373: 'OSTRICH',
 374: 'OVENBIRD',
 375: 'OYSTER CATCHER',
 376: 'PAINTED BUNTING',
 377: 'PALILA',
 378: 'PALM NUT VULTURE',
 379: 'PARADISE TANAGER',
 380: 'PARAKETT  AUKLET',
 381: 'PARUS MAJOR',
 382: 'PATAGONIAN SIERRA FINCH',
 383: 'PEACOCK',
 384: 'PEREGRINE FALCON',
 385: 'PHAINOPEPLA',
 386: 'PHILIPPINE EAGLE',
 387: 'PINK ROBIN',
 388: 'PLUSH CRESTED JAY',
 389: 'POMARINE JAEGER',
 390: 'PUFFIN',
 391: 'PUNA TEAL',
 392: 'PURPLE FINCH',
 393: 'PURPLE GALLINULE',
 394: 'PURPLE MARTIN',
 395: 'PURPLE SWAMPHEN',
 396: 'PYGMY KINGFISHER',
 397: 'PYRRHULOXIA',
 398: 'QUETZAL',
 399: 'RAINBOW LORIKEET',
 400: 'RAZORBILL',
 401: 'RED BEARDED BEE EATER',
 402: 'RED BELLIED PITTA',
 403: 'RED BILLED TROPICBIRD',
 404: 'RED BROWED FINCH',
 405: 'RED CROSSBILL',
 406: 'RED FACED CORMORANT',
 407: 'RED FACED WARBLER',
 408: 'RED FODY',
 409: 'RED HEADED DUCK',
 410: 'RED HEADED WOODPECKER',
 411: 'RED KNOT',
 412: 'RED LEGGED HONEYCREEPER',
 413: 'RED NAPED TROGON',
 414: 'RED SHOULDERED HAWK',
 415: 'RED TAILED HAWK',
 416: 'RED TAILED THRUSH',
 417: 'RED WINGED BLACKBIRD',
 418: 'RED WISKERED BULBUL',
 419: 'REGENT BOWERBIRD',
 420: 'RING-NECKED PHEASANT',
 421: 'ROADRUNNER',
 422: 'ROCK DOVE',
 423: 'ROSE BREASTED COCKATOO',
 424: 'ROSE BREASTED GROSBEAK',
 425: 'ROSEATE SPOONBILL',
 426: 'ROSY FACED LOVEBIRD',
 427: 'ROUGH LEG BUZZARD',
 428: 'ROYAL FLYCATCHER',
 429: 'RUBY CROWNED KINGLET',
 430: 'RUBY THROATED HUMMINGBIRD',
 431: 'RUDDY SHELDUCK',
 432: 'RUDY KINGFISHER',
 433: 'RUFOUS KINGFISHER',
 434: 'RUFOUS TREPE',
 435: 'RUFUOS MOTMOT',
 436: 'SAMATRAN THRUSH',
 437: 'SAND MARTIN',
 438: 'SANDHILL CRANE',
 439: 'SATYR TRAGOPAN',
 440: 'SAYS PHOEBE',
 441: 'SCARLET CROWNED FRUIT DOVE',
 442: 'SCARLET FACED LIOCICHLA',
 443: 'SCARLET IBIS',
 444: 'SCARLET MACAW',
 445: 'SCARLET TANAGER',
 446: 'SHOEBILL',
 447: 'SHORT BILLED DOWITCHER',
 448: 'SMITHS LONGSPUR',
 449: 'SNOW GOOSE',
 450: 'SNOW PARTRIDGE',
 451: 'SNOWY EGRET',
 452: 'SNOWY OWL',
 453: 'SNOWY PLOVER',
 454: 'SNOWY SHEATHBILL',
 455: 'SORA',
 456: 'SPANGLED COTINGA',
 457: 'SPLENDID WREN',
 458: 'SPOON BILED SANDPIPER',
 459: 'SPOTTED CATBIRD',
 460: 'SPOTTED WHISTLING DUCK',
 461: 'SQUACCO HERON',
 462: 'SRI LANKA BLUE MAGPIE',
 463: 'STEAMER DUCK',
 464: 'STORK BILLED KINGFISHER',
 465: 'STRIATED CARACARA',
 466: 'STRIPED OWL',
 467: 'STRIPPED MANAKIN',
 468: 'STRIPPED SWALLOW',
 469: 'SUNBITTERN',
 470: 'SUPERB STARLING',
 471: 'SURF SCOTER',
 472: 'SWINHOES PHEASANT',
 473: 'TAILORBIRD',
 474: 'TAIWAN MAGPIE',
 475: 'TAKAHE',
 476: 'TASMANIAN HEN',
 477: 'TAWNY FROGMOUTH',
 478: 'TEAL DUCK',
 479: 'TIT MOUSE',
 480: 'TOUCHAN',
 481: 'TOWNSENDS WARBLER',
 482: 'TREE SWALLOW',
 483: 'TRICOLORED BLACKBIRD',
 484: 'TROPICAL KINGBIRD',
 485: 'TRUMPTER SWAN',
 486: 'TURKEY VULTURE',
 487: 'TURQUOISE MOTMOT',
 488: 'UMBRELLA BIRD',
 489: 'VARIED THRUSH',
 490: 'VEERY',
 491: 'VENEZUELIAN TROUPIAL',
 492: 'VERDIN',
 493: 'VERMILION FLYCATHER',
 494: 'VICTORIA CROWNED PIGEON',
 495: 'VIOLET BACKED STARLING',
 496: 'VIOLET CUCKOO',
 497: 'VIOLET GREEN SWALLOW',
 498: 'VIOLET TURACO',
 499: 'VISAYAN HORNBILL',
 500: 'VULTURINE GUINEAFOWL',
 501: 'WALL CREAPER',
 502: 'WATTLED CURASSOW',
 503: 'WATTLED LAPWING',
 504: 'WHIMBREL',
 505: 'WHITE BREASTED WATERHEN',
 506: 'WHITE BROWED CRAKE',
 507: 'WHITE CHEEKED TURACO',
 508: 'WHITE CRESTED HORNBILL',
 509: 'WHITE EARED HUMMINGBIRD',
 510: 'WHITE NECKED RAVEN',
 511: 'WHITE TAILED TROPIC',
 512: 'WHITE THROATED BEE EATER',
 513: 'WILD TURKEY',
 514: 'WILLOW PTARMIGAN',
 515: 'WILSONS BIRD OF PARADISE',
 516: 'WOOD DUCK',
 517: 'WOOD THRUSH',
 518: 'WOODLAND KINGFISHER',
 519: 'WRENTIT',
 520: 'YELLOW BELLIED FLOWERPECKER',
 521: 'YELLOW BREASTED CHAT',
 522: 'YELLOW CACIQUE',
 523: 'YELLOW HEADED BLACKBIRD',
 524: 'ZEBRA DOVE'}


if __name__ == "__main__":
    app.run(debug=True)