import requests
import json
import pandas as pd
import time
from timeit import default_timer as timer
import numpy as np
import matplotlib.pyplot as plt
import statistics
from crowpy.crowpy import CrowPy
import json

def get_miles(x, crow):
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
    return x

timesList = []

def runCrowpy(api_username, cartons_filename, output_combined_filename, minSampIndex, maxSampIndex):
    crow = CrowPy(api_username)
    USPSCartons = pd.read_csv(cartons_filename)
    USPSCartons['carton_id'] = USPSCartons['carton_id'].astype(str)
    # USPSCartons = USPSCartons[~USPSCartons['state_abbr'].isin(['AK', 'HI', 'PR', 'VI'])]

    already_processed = pd.read_csv(output_combined_filename)
    already_processed['carton_id'] = already_processed['carton_id'].astype(str)
    processed_carton_ids = already_processed['carton_id'].tolist()
    print(str(len(processed_carton_ids))+" cartons already processed")
    
    USPSCartons = USPSCartons[~USPSCartons['carton_id'].isin(processed_carton_ids)]
    USPSCartons = USPSCartons.reset_index(drop=True)
    print(str(len(USPSCartons))+" cartons left to be processed")
    samp = USPSCartons.iloc[minSampIndex:maxSampIndex]
    
    t1 = timer()
    out = samp.apply(lambda x: get_miles(x, crow),axis=1)
    print(" {} seconds processing".format(round(timer() - t1, 2)))
    print(str(round(sum(timesList),2))+" seconds to process "+str(len(timesList))+" rows processed, avg = "+str(round(statistics.mean(timesList),2))+" sec")
    try:
        out = out[['carton_id','tracking','shipped_at','origin_addr','zipcode','city','state_abbr','country','ground_miles', 'air_miles', 'shipping_method', 'weight']]
    except Exception as e:
        print(out)
        print(str(e))
    
    try:
        # df1 = pd.DataFrame([[np.nan] * 12])
        # df1.to_csv(output_combined_filename, mode='a', index=False, header=None)
        out.to_csv(output_combined_filename, mode='a', index=False, header=False)
    except Exception as e:
        print("Unable to write to csv", str(e))
    
    return out