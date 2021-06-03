from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import logging,time,os
import geopy
import requests

#URL tp download chrome driver - https://chromedriver.chromium.org/downloads

LOG = logging.getLogger('Common_utilities')

from random import randint

def random_with_n_digits(n):
    LOG.info('random_with_N_digits')
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)

def get_chrome_driver_path():
    LOG.info('get_chrome_driver_path')
    paths = os.environ['Path'].split(';')
    path = [p for p in paths if p.count('chromedriver') > 0][0]
    chrome_driver_path = path.replace('\\','/') + '/chromedriver.exe'
    LOG.debug('Chrome Driver path is {0}'.format(chrome_driver_path))
    return chrome_driver_path

def get_current_latitude_longitude():
    LOG.info('get_current_latitude_longitude')
    """
    start-maximized: Opens Chrome in maximize mode
    incognito: Opens Chrome in incognito mode
    headless: Opens Chrome in headless mode
    disable-extensions: Disables existing extensions on Chrome browser
    disable-popup-blocking: Disables pop-ups displayed on Chrome browser
    make-default-browser: Makes Chrome default browser
    version: Prints chrome browser version
    disable-infobars: Prevents Chrome from displaying the notification 'Chrome is being controlled by automated software
    """
    options = Options()
    #options.headless = True
    #options.add_argument("--headless")
    options.add_argument("--use--fake-ui-for-media-stream")
    chrome_driver_path = get_chrome_driver_path()
    driver = webdriver.Chrome(executable_path=chrome_driver_path,options=options) #Edit path of chromedriver accordingly
    timeout = 7
    driver.get("https://mycurrentlocation.net/")
    wait = WebDriverWait(driver, timeout)
    time.sleep(3)
    longitude = driver.find_elements_by_xpath('//*[@id="longitude"]') #Replace with any XPath
    longitude = [x.text for x in longitude]
    longitude = longitude[0]
    latitude = driver.find_elements_by_xpath('//*[@id="latitude"]')
    latitude = [x.text for x in latitude]
    latitude = latitude[0]

    driver.close()
    return (latitude,longitude)

def get_public_ip_addr():
    LOG.info('get_public_ip_addr')
    ip = requests.get('https://api.ipify.org').text
    print('My public IP address is: {}'.format(ip))

def get_location_details(loc_cordinates=None):
    LOG.info('get_location_details')

    # lat_lang for Testing = 19.1967015,73.2006444
    if loc_cordinates is None:
        loc_cordinates = get_current_latitude_longitude()
    geolocator = geopy.Nominatim(user_agent='my-cowin')
    location = geolocator.reverse(loc_cordinates)
    print(location.raw)
    state = location.raw['address']['state'] if 'state' in location.raw['address'] else None
    district = location.raw['address']['state_district'] if 'state_district' in location.raw['address'] else None
    city = location.raw['address']['city'] if 'city' in location.raw['address'].keys() else location.raw['address']['town'] if'town' in location.raw['address'] else None
    postcode = location.raw['address']['postcode'] if 'postcode' in location.raw['address'] else None
    return {'state':state, 'district':district, 'city':city}

if __name__ == '__main__':
    loc_cordinates = get_current_latitude_longitude()
    print(loc_cordinates)
    if len(loc_cordinates):
        loc_details = get_location_details(loc_cordinates)
        print(loc_details)