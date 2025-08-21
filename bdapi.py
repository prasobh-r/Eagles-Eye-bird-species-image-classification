import requests
from io import BytesIO
import urllib.request
from PIL import Image
import json
import random
import google.generativeai as palm
import datetime
palm.configure(api_key="AIzaSyAqJ8w5cn-Rq2LlzONPhVY6Z7e73iAYjO8")

def extract_link(json):
    return json["items"][0]["link"]


def birdofday():
    with open('bird_species.json', 'r') as f:
        data = json.load(f)
    common_names = list(data.keys())
    common_name = random.choice(common_names)
    print("Random common name:", common_name)
    # Google API Section
    googleUrl = "https://www.googleapis.com/customsearch/v1"
    google_Payload = {
        'key': 'AIzaSyA1bY0gkHoSRZFVMHoGQL3jcFFcX9XuTtU',
        'cx': 'f4d08834ed79a4183',
        'q': common_name+" ebird",
        'num': 1,
        'searchType': 'image'
        }
    response = requests.get(googleUrl, params=google_Payload)
    birdImgLink = extract_link(response.json())
    response = requests.get(birdImgLink)
    if response.status_code == 200:
        try:
            # Open the image from the response content
            img = Image.open(BytesIO(response.content))
            
            # Save the image to a file
            img.save(r"static\bird.jpg")
        except Exception as e:
            print(f"An exception occurred: {e}")
    else:
        print(f"Failed to download the image. Status code: {response.status_code}")
    
    return common_name

def birdofdayupdate():
    try:
        with open('birdofday.json', 'r+') as file:
            data = json.load(file)
            if data['date'] == datetime.date.today().strftime('%Y-%m-%d'):
                pass
            else:
                with open('birdofday.json', 'w') as file:
                    bodname = birdofday()
                    des = palm.generate_text(prompt="short description about " + bodname + " bird in 100 words")
                    bdes = des.candidates[0]['output']
                    bdate = datetime.date.today().strftime('%Y-%m-%d')
                    bdict = {
                        'cname': bodname,
                        'des': bdes,
                        'date': bdate
                    }
                    json.dump(bdict, file)
    except json.JSONDecodeError:
        with open('birdofday.json', 'w') as file:
            bodname = birdofday()
            des = palm.generate_text(prompt="short description about " + bodname + " bird in 100 words")
            bdes = des.candidates[0]['output']
            bdate = datetime.date.today().strftime('%Y-%m-%d')
            bdict = {
                'cname': bodname,
                'des': bdes,
                'date': bdate
            }
            json.dump(bdict, file)

birdofdayupdate()

