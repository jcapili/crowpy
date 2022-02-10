from usps import USPSApi
from geopy.geocoders import Nominatim
import geopy.geocoders
from geopy import distance
from datetime import datetime, timedelta
from tqdm.auto import trange
from tqdm import tqdm
import requests, re, os, ssl, certifi
import pandas as pd
import json
from timeit import default_timer as timer
import math

zipcodes = pd.read_csv("spree_public_zipcodes.csv", dtype={'zipcode': 'str', 'city': 'str', 'lat': float, 'lon':float, 'state':str})
zipcodes['city'] = zipcodes['city'].str.upper()
zipcodes = zipcodes.dropna(subset=['lat', 'lon'])

class CrowPy(object):
    # https://github.com/geopy/geopy/issues/124
    ctx = ssl.create_default_context(cafile=certifi.where())
    geopy.geocoders.options.default_ssl_context = ctx
    geolocator = Nominatim(user_agent="CrowPy")

    # https://en.wikipedia.org/wiki/Sectional_center_facility
    sectionalCenterFacilities = {
        'CA':{
            'NORTH BAY': 'San Francisco',
            'CITY OF INDUSTRY': 'West Covina'
        },
        'CT':{
            'SOUTHERN': 'Wallingford',
        },
        'FL': {
            'SEMINOLE-ORLANDO': 'Orlando',
            'FORT MEYERS': 'Fort Myers'
        },
        'GA':{
            'ATLANTA-PEACHTREE': 'Atlanta',
        },
        'IL': {
            'SOUTH SUBURBAN': 'Bedford Park',
            'FOX VALLEY': 'Aurora',
            'QUAD CITIES': 'Davenport'
        },
        'ME': {
            'SOUTHERN': 'Portland',
            'EASTERN': 'Hampden'
        },
        'MD': {
            'SOUTHERN MARYLAND': 'Waldorf',
            'SOUTHERN': 'Waldorf',
            'SUBURBAN MARYLAND': 'Gaithersburg',
            'EASTERN SHORE': 'Easton'
        },
        'MA': {
            'CENTRAL MASSACHUSETTS': 'Shrewsbury',
            'MIDDLESEX-ESSEX': 'North Reading'
        },
        'MI': {
            'METROPLEX': 'Pontiac'
        },
        'MO': {
            'MID-MO': 'Columbia'
        },
        'NC': {
            'MID CAROLINA-CHARLOTTE': 'Charlotte'
        },
        'NJ': {
            'SOUTH JERSEY': 'Atlantic City'
        },
        'NY': {
            'WESTCHESTER': 'White Plains',
            'WESTERN NASSAU': 'Gardern City',
            'MID-HUDSON': 'Newburgh',
            'METRO': 'Chelsea',
            'NORTHWEST ROCHESTER':'Rochester'
        },
        'PA': {
            'LEHIGH VALLEY': 'Bethlehem'
        }
    }
    
    cityStateOptions = {"WEST FARGO": ("West Fargo", "ND"),
                    "ATLANTA NORTH METRO": ("Atlanta", "GA"),
                    "SALT LAKE CITY": ("Salt Lake City", "UT"),
                    "PORTLAND": ("Portland", "OR"),
                    "ERIE": ("Erie", "PA"),
                    "ALTOONA": ("Altoona", "PA")}

    APO_zips = ['96269','96672','09266','09002','09003','09004','09005','09006','09008','09009','09010','09011','09012','09013','09014','09016','09017','09018','09020','09021','09028','09034','09044','09046','09049','09053','09054','09055','09060','09067','09068','09069','09079','09090','09094','09095','09096','09101','09104','09107','09112','09114','09123','09125','09126','09128','09131','09136','09138','09139','09140','09142','09154','09172','09173','09177','09180','09186','09211','09214','09226','09227','09240','09242','09250','09261','09263','09264','09302','09304','09305','09306','09307','09308','09309','09314','09315','09316','09317','09318','09319','09320','09321','09322','09323','09330','09333','09337','09340','09343','09347','09348','09351','09352','09354','09355','09356','09357','09365','09366','09378','09381','09401','09403','09421','09447','09454','09456','09459','09461','09463','09464','09468','09469','09470','09494','09496','09497','09522','09533','09541','09542','09544','09545','09600','09602','09603','09604','09605','09606','09610','09613','09630','09633','09634','09635','09643','09647','09702','09703','09704','09705','09706','09708','09711','09714','09717','09719','09720','09722','09724','09725','09732','09735','09743','09745','09749','09751','09752','09753','09754','09755','09756','09758','09760','09780','09789','09800','09801','09803','09804','09810','09815','09818','09821','09822','09824','09829','09832','09833','09839','09848','09851','09852','09853','09855','09858','09861','09863','09868','09876','09877','09890','09898','09901','09903','09904','09908','09909','09910']

    def __init__(self, usps_id ):
        self.usps = USPSApi(usps_id)
        self.chunkList = []

    def geolocate(self, location_dict, tries = 0):
        """
        Wrapper function for geolocator 
        """
        if tries == 3:
            return None
        try:
            return self.geolocator.geocode(location_dict, country_codes='us', timeout=15)
        except:
            return self.geolocate(location_dict, tries+1)

    def calculateMiles(self, tracking, osrm, printSteps = False, debugMode=False):
        """
        Calculate the number of plane/truck miles from a USPS shipment

        Inputs
            -tracking: A str of the USPS tracking number
        Outputs
            -truckMiles: An int of the # of miles the package traveled in a truck
            -planeMiles: ^ Same but a plane
        """
        # print tracking
        track = self.usps.track(tracking)
        if 'Error' in track.result['TrackResponse']['TrackInfo']:
            print("Tracking label is invalid:", tracking)
            return 0, 0
        
        if 'TrackSummary' not in track.result['TrackResponse']['TrackInfo'].keys():
            print("Package has not yet been delivered", tracking)
            return 0, 0

        summaryEvent = track.result['TrackResponse']['TrackInfo']['TrackSummary']
        if 'Delivered' not in summaryEvent['Event']:
            print("Package has not yet been delivered", tracking)
            return 0, 0

        try:
            events = track.result['TrackResponse']['TrackInfo']['TrackDetail']
        except:
            print("Unable to track the miles for this package: Tracking details unavailable", tracking)
            return 0, 0

        planeMiles = 0
        truckMiles = 0
        routeData = [] # Each element is a tuple with the latitude, longitude, time string, city, and state of each relevant destination

        # Make the events in chronological order
        try:
            events.reverse()
        except AttributeError:
            events = [events] # make events a list
        city = ''
        state = ''
        # Extrapolate coordinates and datetime of each relevant event
        for e in events:
            # print(e)
            if e['EventZIPCode'] is not None:
                t1 = timer()
                zipCode = e['EventZIPCode']
                # print("zipCode", str(zipCode), "event city", e['EventCity'])

                if e['Event'] != 'Out for Delivery':
                    # location = self.locate(zipCode)
                    if debugMode:
                        print("searching by zip", zipCode)
                    try:
                        lat, lon, city, state = zipcodes.loc[zipcodes['zipcode'] == zipCode.strip(), ['lat','lon', 'city', 'state']].iloc[0]
                    except:
                        # zip was not found in zipcodes df - get using geopandas
                        location = self.locate(zipCode)
                        lat, lon = location.latitude, location.longitude
                        loc = self.geolocator.reverse((lat, lon))
                        loc = loc.raw['address'] 
                        if "city" in loc.keys() and "state" in loc.keys():
                            city = loc['city']
                            state = loc['state']
                    # if location:
                    # Safeguard in case this event doesn't have a time, skip this statement and use the time from the prev event
                    if e['EventTime']:
                        time = e['EventTime']
                    # routeData.append([location.latitude, location.longitude, e['EventDate']+" "+time])
                    # print("Location found from zipcode", zipCode, str(round(timer()-t1, 2)), "sec")
                    routeData.append([lat, lon, e['EventDate']+" "+time, city, state])
                    if debugMode:
                        print("Lat lon found from zipcode", zipCode, str(round(timer()-t1, 2)), "sec")
            else:
                if e['EventCity'] is not None and 'DISTRIBUTION CENTER' in e['EventCity']:
                    if 'INTERNATIONAL' in e['EventCity']:
                        return 0, 0
                    sep = ' DISTRIBUTION CENTER'
                    if 'NETWORK' in e['EventCity']:
                        sep = ' NETWORK DISTRIBUTION CENTER'

                    area = e['EventCity'].split(sep)[0]
                    area = area.strip()
                    # print("area:", area)
                    
                    prevCity = city
                    prevState = state
                    
                    if area in self.cityStateOptions.keys():
                        city, state = self.cityStateOptions[area]
                    else:
                        city = area[:len(area)-3]
                        state = area.replace(city+' ', '')
                    # location = self.geolocate({"city":city,"state":state})
                    # print("city:", city, "state:", state) 
                    
                    try: # Get the city from dict
                        city = self.sectionalCenterFacilities[state][city]
                    except KeyError:
                        # print("KeyError")
                        pass
                    
                    try:
                        lat, lon = zipcodes.loc[(zipcodes['city'] == city.upper().strip()) & (zipcodes['state'] == state.strip()), ['lat', 'lon']].iloc[0]
                        
                        routeData.append([lat, lon, e['EventDate']+" "+e['EventTime'], city.strip(), state.strip()])
                        if debugMode:
                            print("Lat lon " + str(lat) +" " + str(lon)+ " found from distribution center city "+city+", "+state+" - " + str(round(timer()-t1, 2))+ " sec")
                    except:
                        # print("No matching city, ST found for " + city + ", " + state)
                        # return 0, 0
                         # if city, state the same as previous, no need to geolocate again
                        if prevCity == city:
                            if debugMode:
                                print("prev city equals city", prevCity)
                            routeData.append([location.latitude, location.longitude, e['EventDate']+" "+e['EventTime'], city.strip(), state.strip()])
                        else:
                            location = self.geolocate({"city":city,"state":state})

                            if not location:
                            # if not lat:
                                if state == "PR":
                                    realCity = "Catano"
                                    state = ""
                                else: 
                                    try: # Get the city the hard way
                                        realCity = self.sectionalCenterFacilities[state][city]
                                    except:
                                        printStr = str(city) + ', ' + str(state) + ', ' + str(tracking)
                                        print("Unable to get sectional center facility for", printStr)
                                        continue
                                location = self.geolocate({"city":realCity,"state":state})
                                if not location:
                                    print("No matching city found for " + city + " " + state)
                                    return 0,0
                                if debugMode:
                                    print("Location found from sectional center facility in " + city + ", " + state)
                            else:
                                if debugMode:
                                    print("Location found from distribution center geolocate (" + city + ", " + state + ") " + str(round(timer()-t1, 2))+ " sec")

                            routeData.append([location.latitude, location.longitude, e['EventDate']+" "+e['EventTime'], city.strip(), state.strip()])
                            # routeData.append([location.latitude, location.longitude, e['EventDate']+" "+e['EventTime']])
                            # routeData.append([lat, lon, e['EventDate']+" "+e['EventTime']])
                            

        # Add delivered event to routeData
        summaryEvent = track.result['TrackResponse']['TrackInfo']['TrackSummary']
        zipCode = summaryEvent['EventZIPCode']
        if debugMode:
            print("summaryEvent zip code", str(zipCode))
        
        # location = self.geolocate({"postalcode":zipCode})
        # if location:
        try:
            lat, lon, city, state = zipcodes.loc[zipcodes['zipcode'] == zipCode.strip(), ['lat','lon', 'city', 'state']].iloc[0]  
            routeData.append([lat, lon, summaryEvent['EventDate']+" "+summaryEvent['EventTime'], city.strip(), state.strip()])
        except:
            print("unable to get summary event lat lon for zip", str(zipCode))
        
        if osrm:
            return self.translateRouteData(routeData, osrm=True, printSteps = printSteps)
        else:
            return self.translateRouteData(routeData, osrm=False, printSteps = printSteps)
        
    def locate(self, zipCode, jump = -1):
        """
        Return the Geopy location object of a given zipcode. If the API can't find a US zip code that matches the original, use recursion
        to find the nearest zip code that works and return that location object instead. Recursion works by sequentially jumping back and forth
        between zip codes above and below the original one to find the nearest one

        Inputs
            -zipCode: String of a US zip code
            -jump: an integer indicating the next zip code to check if this current zip code isn't found
        Outputs
            -location object or 'None' if the function is accidentally given a faulty value
        """
        # Safeguard to prevent infinite recursion
        if abs(jump) > 20:
            return None

        location = self.geolocate({"postalcode":zipCode})

        if location:
            return location
        else:
            newZip = str(int(zipCode) + jump)

            # The leading '0's might have been erased in the int() call, so restore them to the string
            if len(newZip) < 5:
                for _ in range(5-len(newZip)):
                    newZip = '0' + newZip

            if jump < 0:
                return self.locate(newZip, (jump*-1)+1)
            else:
                return self.locate(newZip, (jump*-1)-1)
    
    
    def getCityStateFromLatLon(self, locTuple):
        loc = self.geolocator.reverse(locTuple)
        loc = loc.raw['address'] 
        if "city" in loc.keys() and "state" in loc.keys():
            loc = loc['city'] + ", " + loc['state']
        elif "town" in loc.keys() and "state" in loc.keys():
            loc = loc['town'] + ", " + loc['state']
        elif "county" in loc.keys() and "state" in loc.keys():
            loc = loc['county'] + ", " + loc['state']
        elif "city_district" in loc.keys() and "state" in loc.keys():
            loc = loc['city_district'] + ", " + loc['state']
        elif "postcode" in loc.keys() and "state" in loc.keys():
            loc = loc['postcode'] + ", " + loc['state']
        # elif "city" in loc.keys() and "county" in loc.keys():
        #     loc = loc['city'] + ", " + loc['county']
        # elif "city_district" in loc.keys() and "county" in loc.keys():
        #     loc = loc['city_district'] + ", " + loc['county']
        # else:
        #     print(json.dumps(loc))
        return loc
    
    def translateRouteData(self, routeData, osrm, printSteps):
        """
        Split the route data into chunks traveled by plane and truck. 
        Distances are categorized based on distance (>500 is a plane)
        
        Inputs
            -routeData = a list of lists where each element of the child list is in the following format:
                [latitude, longitude, datetime of event]
        Outputs
            -truckMiles = float of # miles traveled via truck according to shortest route using osrm
            -planeMiles = float of # miles traveled via plane according to Geopy distance function
        """
        truckMiles = 0
        planeMiles = 0
        
        # The following pieces of data are from https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3835347/
        detourIndex = 1.417 # Slope of travel distance (km) vs straight-line distance (km)
        travelTimeIndex = 1.056 # Slope of travel time (min) vs travel distance (km), not in use
        # print(routeData)
        
        for i in range(len(routeData)-1):
            start = routeData[i]
            startTuple = (start[0],start[1])
            dest = routeData[i+1]
            destTuple = (dest[0], dest[1])
            
            # print("start:", start, " dest:", dest)
            
            if startTuple == destTuple:
                continue
                
            hours = (datetime.strptime(dest[2], '%B %d, %Y %I:%M %p') - datetime.strptime(start[2], '%B %d, %Y %I:%M %p')).total_seconds()/float(3600)
            miles = distance.distance(startTuple, destTuple).miles
            
            # get a readable version of start & end location for debugging
            # startLoc = self.getCityStateFromLatLon(startTuple)
            # endLoc = self.getCityStateFromLatLon(destTuple)
            startLoc = start[3].title() + ", " + start[4]
            endLoc = dest[3].title() + ", " + dest[4]
            
            # if not isinstance(startLoc, str):
            #     print("Unable to locate start loc:", startLoc)
            #     continue
            # if not isinstance(endLoc, str):
            #     print("Unable to locate end loc:", endLoc)
            #     continue

            if hours > 0:
                groundMiles = miles * detourIndex
                mph = miles / hours

                if (mph > 55) | (start[4] in ['HI', 'PR','VI']) | (dest[4] in ['HI', 'PR','VI']):# and state is HI, PR, VI, ...
                # if miles > 500:
                    if printSteps:
                        print(str(round(miles,1))+ " air miles from "+ startLoc + " to "+ endLoc + " (over " + str(round(hours,1)) + " hours, avg "+ str(round(mph, 1)) + " mph)")
                    planeMiles += miles
                else:
                    if osrm: ## get actual route using OSRM API to map a car route
                        url = "http://router.project-osrm.org/route/v1/car/"+str(startTuple[1])+","+str(startTuple[0])+";"+str(destTuple[1])+","+str(destTuple[0])+"?overview=false"
                        r = requests.get(url)
                        my_bytes_value = r.content

                        # get a recommended route
                        routes = json.loads(my_bytes_value.decode('utf8'))
                        try:
                            route = routes.get("routes")[0]
                        except:
                            print("No ground route found between "+startLoc+" and "+endLoc)
                            return 0,0
                        # convert meters to miles
                        miles = route['distance']/1609.34
                        if printSteps:
                            print(str(round(miles,1))+ " ground miles from "+ startLoc + " to "+ endLoc+ " (over " + str(round(hours,1)) + " hours, avg "+ str(round(mph, 1)) + " mph)")
                        truckMiles += miles
                    else:
                        if printSteps:
                            print(str(round( groundMiles ,1))+ " ground miles from "+ startLoc + " to "+ endLoc+ " (over " + str(round(hours,1)) + " hours, avg "+ str(round(mph, 1)) + " mph)")
                        truckMiles += groundMiles
                    
        return truckMiles, planeMiles

    def calculateCSVMiles(self, input_path, output_path, google = False, resetChunks = True):
        dataIterator = pd.read_csv(str(input_path), chunksize=100)

        if resetChunks:
            self.chunkList = []

        chunkList = self.chunkList

        # Wrapper function for calculate miles so that the data processing isn't messed up by one erroneous tracking number
        def wrapper(tracking, google):
            try:
                return pd.Series(list(self.calculateMiles(tracking, google)))
            except:
                return pd.Series([0,0])

        lambdafunc = lambda row: wrapper(row['trackingNumber'], google)
        length = max(len(pd.read_csv(str(input_path)))/100, 1)
        counter = 1
        tqdm.pandas(desc="Progress")

        for chunk in dataIterator:
            if counter < len(chunkList):
                counter += 1
                continue

            printStr = "Batch #" + str(counter) + " of " + str(length)
            print(printStr)
            chunkData = chunk[~chunk['zipCode'].str[:5].isin(self.APO_zips)]
            chunkData[['truckMiles','planeMiles']] = chunkData.progress_apply(lambdafunc, axis=1)
            chunkList.append(chunkData)
            counter += 1
            
        orderData = pd.concat(chunkList)
        orderData.to_csv(str(output_path))
