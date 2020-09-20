import json
import pprint
import urllib.request


class Weather:
    def __init__(self, owm_key):
        self.owm_key = owm_key
        self.units = 'metric'  # ['imperial']
        self.pp = pprint.PrettyPrinter(indent=4)

    def update_owm(self, units, search):
        search = str(search).split(',')
        id_num = ''
        state = ''

        if len(search) > 2:
            city = search[0]
            country = search[1].strip(' ')
            id_num = search[2].strip(' id:')
            url_str = f'http://api.openweathermap.org/data/2.5/weather?id={id_num}&appid={self.owm_key}&units={self.units}'
            print(id_num)

        else:
            city, country = search
            country = country.strip(' ')
            url_str = f'http://api.openweathermap.org/data/2.5/weather?q={city},{state},{country}&appid={self.owm_key}&units={self.units}'
            

        self.units = str(units)
        
        print(city, country)
        print(url_str)

        try:
            source = urllib.request.urlopen(url_str).read()
        except Exception:
            print("WARNING: Request to OWM failed, check your API KEY!!")
        # converting JSON data to a dictionary
        weather_dict = json.loads(source)

        if weather_dict['cod'] == 200:
            weather_status = {
                'city': str(city),
                'cc': str(country),
                'temp': str(round(weather_dict['main']['temp'], 1)) + ' &#176;',
                'temp_max': str(round(weather_dict['main']['temp_max'], 1)) + ' &#176;',
                'temp_min': str(round(weather_dict['main']['temp_min'], 1)) + ' &#176;',
                'temp_feel': str(round(weather_dict['main']['feels_like'], 1)) + ' &#176;',
                'humidity': str(weather_dict['main']['humidity']) + ' %',
                'wind_speed': str(weather_dict['wind']['speed']) + ' m/s',
                'pressure': str(weather_dict['main']['pressure']) + ' hPa',
                'status': str(weather_dict['weather'][0]['main']),
                'detailed_status': str(weather_dict['weather'][0]['description']),
                'icon': str(weather_dict['weather'][0]['icon']),
            }

            return weather_status

        else:
            return {}

    def search_locations(self, search_field):

        search = str(search_field).split(',')
        if len(search) > 1:
            city, country = search
            country = country.strip(' ')
        else:
            city = search[0]
            country = ''
        
        print(city, country)
        state = ''
        results = []

        url_str = f'http://api.openweathermap.org/data/2.5/find?q={city},{state},{country}&appid={self.owm_key}'
        print(url_str)
        try:
            source = urllib.request.urlopen(url_str).read()
        except Exception:
            print("WARNING: Request to OWM failed, check your API KEY!!")

        # converting JSON data to a dictionary
        weather_dict = json.loads(source)

        if int(weather_dict['cod']) == 200:
            print('Got it')
            print(weather_dict)
            i = 0
            for i in range(0, weather_dict['count']):
                results.append(weather_dict['list'][i]['name'] + ',' + weather_dict['list'][i]['sys']['country'] + ', id: ' + str(weather_dict['list'][i]['id']))
                i += 1
        print('here is results')
        print(results)

        
        return results
