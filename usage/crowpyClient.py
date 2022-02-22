import pandas as pd
import time
from timeit import default_timer as timer
import statistics
from crowpy.crowpy import CrowPy

def get_miles(x, rowIndex, crow):
    start = time.time()
    try:
        groundMiles, airMiles, routeDataDetails = crow.calculateMiles(x['tracking'], osrm=True, printSteps=False)
        end = time.time()
        timesList.append(end - start)
        print(str(rowIndex),end=' ')
        x['ground_miles'], x['air_miles'], x['route_data_details_list'] = groundMiles, airMiles, routeDataDetails
        return x
    except Exception as e:
        end = time.time()
        timesList.append(end - start)
        print(str(rowIndex),end=' ')
        routeDataDetails = 'error:' + str(e) + " tracking: " + str(x['tracking'])
        x['ground_miles'], x['air_miles'], x['route_data_details_list'] = 0, 0, routeDataDetails
        return x

# keep track of seconds it takes to process each tracking number
timesList = []

def runCrowpy(api_username, cartons_filename, output_combined_filename, desired_output_columns, minSampIndex, maxSampIndex):
    """
        Take a sample of a given size from a file containing tracking numbers and append results to an output CSV. For example, sample the first 100 rows using minSampIndex=0 and maxSampIndex=100. Creates 3 additional columns for ground_miles, air_miles, and route_data_details_list.

        Inputs
            - api_username: 
            - cartons_filename: filename of cartons to be processed. Expects two columns
                - carton_id: allows us to keep this file intact but filter out carton's we've already processed
                - tracking: 
            - output_combined_filename: filename of processed cartons. Will not write headers.
            - desired_output_columns: list of columns to include in the output file; should align with headers already present in output file. The created columns (ground_miles, air_miles, and route_data_details_list) should be included in this list if desired in output file.
            - minSampIndex: inclusive index of first element of sample
            - maxSampIndex: exclusive index of last element of sample
        Outputs
            - out: dataframe containing desired columns.
        """
    crow = CrowPy(api_username)
    USPSCartons = pd.read_csv(cartons_filename)
    USPSCartons['carton_id'] = USPSCartons['carton_id'].astype(str)

    already_processed = pd.read_csv(output_combined_filename)
    already_processed['carton_id'] = already_processed['carton_id'].astype(str)
    processed_carton_ids = already_processed['carton_id'].tolist()
    print(str(len(processed_carton_ids))+" cartons already processed")
    
    USPSCartons = USPSCartons[~USPSCartons['carton_id'].isin(processed_carton_ids)]
    USPSCartons = USPSCartons.reset_index(drop=True)
    print(str(len(USPSCartons))+" cartons left to be processed")
    samp = USPSCartons.iloc[minSampIndex:maxSampIndex]
    
    t1 = timer()
    out = samp.apply(lambda x: get_miles(x, x.name, crow),axis=1)
    print(str(round(sum(timesList),2))+" seconds to process "+str(len(timesList))+" rows processed, avg = "+str(round(statistics.mean(timesList),2))+" sec")

    try:
        # get subset of only the desired output columns
        out = out[desired_output_columns]
    except Exception as e:
        print(str(e))
        print(out)
        return out
    
    try:
        # append new rows to CSV
        out.to_csv(output_combined_filename, mode='a', index=False, header=False)
    except Exception as e:
        print("Unable to write to csv", str(e))
    
    return out