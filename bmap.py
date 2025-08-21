import folium
from geopy.geocoders import Nominatim
import json
import google.generativeai as palm

palm.configure(api_key="AIzaSyAqJ8w5cn-Rq2LlzONPhVY6Z7e73iAYjO8")


def bmap(result):
    with open('bird_countries.json', 'r') as file:
        bird_countries = json.load(file)
    countries = bird_countries[result]
    print(countries)

    list =[]
    for country in countries:
        des = palm.generate_text(prompt="return all possible locations  of {} in {} only names not bold and in a single line with separated by comas do not give any headings or descriptions".format(result,country))
        bdes = des.candidates[0]['output']
        symbols_to_remove = ['*', '[',']']
        for symbol in symbols_to_remove:
            bdes = bdes.replace(symbol, '')
        loc = bdes.split(',')
        for i in loc:
            list.append(i)
    print(list)

    geolocator = Nominatim(user_agent="bird_mapping")
    center = geolocator.geocode(countries[0])
    mymap = folium.Map(location=[center.latitude, center.longitude], zoom_start=3, control_scale=True, prefer_canvas=True, tiles='OpenStreetMap', lang='en')
    geolocator = Nominatim(user_agent="bird_mapping")
    for loc in list:
        location = geolocator.geocode(loc)
        if location:
            icon_image = "static/birdhouse.png"
            icon = folium.CustomIcon(icon_image,icon_size=(32, 32))
            folium.Marker(location=[location.latitude, location.longitude], icon=icon, popup=loc).add_to(mymap)
    mymap.save(r"static\birdmap.html")
    print("bmap end")
