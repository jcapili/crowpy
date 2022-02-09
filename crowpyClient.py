import requests
import json
import pandas as pd
import time
from timeit import default_timer as timer
import numpy as np
import matplotlib.pyplot as plt
import statistics
from crowpy.crowpy.crowpy import CrowPy
import json
crow = CrowPy("720CANDL4823")

def get_miles(x):
    start = time.time()
    try:
        groundMiles, airMiles = crow.calculateMiles(x['tracking'], osrm=True, printSteps=False)
    except Exception as e:
        return 'error:' + str(e) + " tracking: " + str(x['tracking'])
    x['ground_miles'] = groundMiles
    x['air_miles'] = airMiles
    end = time.time()
    timesList.append(end - start)
    print(str(x.name),end=' ')
    # print(str(x.name)+", "+str(round(end - start,1))+" sec, ",end='')
    return x

def runCrowpy(cartons_filename, output_filename):
    # 2/7/2022 read fresh data
    USPSCartons = pd.read_csv('usps_cartons_120_days_from_02_07.csv')
    USPSCartons['carton_id'] = USPSCartons['carton_id'].astype(str)
    USPSCartons['origin_addr'] = np.where(np.isin(USPSCartons['stock_location_id'], [2, 3, 4, 5]),'1717 East Lawson St, Durham, NC 27703','911 Linda Way, Sparks, NV 89431')
    USPSCartons = USPSCartons[~USPSCartons['state_abbr'].isin(['AK', 'HI', 'PR', 'VI'])]

    already_processed = pd.read_csv("out_crowpy_osrm.csv")
    already_processed = already_processed[already_processed['miles_calc'] == 'mixed']
    processed_carton_ids = already_processed['carton_id'].tolist()
    print(str(len(processed_carton_ids))+" cartons already processed")