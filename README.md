## CrowPy
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/crowpy)](https://pypi.org/project/crowpy/)
![PyPI](https://img.shields.io/pypi/v/crowpy?color=brightgreen)
[![PyPI - License](https://img.shields.io/pypi/l/crowpy)](https://github.com/jcapili/crowpy/blob/master/LICENSE)

CrowPy (pronounced "*crow-pie*") uses Python to calculate the number of plane and truck miles traveled to deliver a USPS package. The name is a pun on the phrase "As the crow flies."

CrowPy was created to allow companies to easily track how many aggregate miles their packages have traveled in order to offset the associated carbon emissions :truck::package::evergreen_tree:

Here's a list of a few companies that can actually help you offset your emissions:
* [Pachama](https://pachama.com/)
* [Carbonfund.org](https://carbonfund.org/)
* [Wren](https://projectwren.com/)
* [Terrapass](https://www.terrapass.com/)

## Installation
Install using pip
```
pip install crowpy
```
Before you begin, you'll also need to register for a USPS API key [here](https://www.usps.com/business/web-tools-apis/welcome.htm).

## Usage
**Single Tracking Numbers**
```python
from crowpy import *

cp = CrowPy("your_USPS_API_key")
cp.calculateMiles("your_tracking_number")
```
*Sample Output:* (283.06504755633324, 0)
This function returns a tuple with the truck miles and plane miles, respectively. 

To get the data according to Google Maps, use the same function, and set the `google` flag to `True`:
```python
from crowpy import *

cp = CrowPy("your_USPS_API_key")
cp.calculateMiles("your_tracking_number", True)
```
This function returns the same tuple but with truck miles according to Google Maps, and it prints links similar to [this one](https://www.google.com/maps/dir/+34.1341,-118.3215/+33.9850,-118.4695/+33.8121,-117.9190/) with the corresponding driving data.

<img src="images/map_example.png" alt="Google Maps example" width="600"/>

**CSV's**
```python
from crowpy import *

cp = CrowPy("your_USPS_API_key")
cp.calculateCSVMiles("~/path/to/input/CSV", "~/path/to/output/CSV")
```
Given a CSV with `trackingInfo` and `zipCode` columns, this function appends `truckMiles` and `planeMiles` columns.

There are 2 default inputs to this function that can be changed:
* The `google` flag, which defaults to `False`, uses Google Maps to calculate the truck miles. Here's an example of how to change it:
```python
cp.calculateCSVMiles("~/path/to/input/CSV", "~/path/to/output/CSV", True)
```
* There's also a `resetChunks` flag, which always defaults to `True`. This function chunks large CSV's into batches of 100, so setting the `resetChunk` flag to `False` ensures that the function doesn't erase whatever data it has already collected. So if your CSV is 200 rows and the tracking number in row 150 errors due to a Geopy or USPS timeout error, set the flag to `False` and the function will pick up from the 101st row. Here's an example of how to change it:
```python
cp.calculateCSVMiles("~/path/to/input/CSV", "~/path/to/output/CSV", False, False)
```
*Note*: The data is saved per CrowPy instance, so if the original CrowPy instance is overwritten or reset, the associated data will also be lost. Therefore this function works best in a shell as opposed to a script. Use Ctrl+Z to interrupt this function if necessary.

## Accuracy
There is no third-party entity I know of that can be used to verify the accuracy of these functions. However, these functions have been tested and spot checked using Google Maps, which is probably the foremost tool for verifying the accuracy.

The most likely point of inaccuracy is calculating driving distance, which is often very different from the distance as the crow flies (hence the name of this project). So the driving miles are calculated based on the 1.417 detour index from [this](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3835347/) national study, where the detour index defined as travel distance divided by straight-line distance. 

<img src="images/study.png" alt="Distance study" width="500"/>

The "google" boolean flag in the `calculateMiles` function will provide links to Google Maps routes that can be used to spot check the accuracy of this detour index on a case-by-case basis. But based on past tests, the detour index calculations are typically an overestimate of the Google Maps calculations, which often is preferred so that you can be relatively confident you're *totally* offsetting all shipping-related emissions.

## Known Bugs
* There are a *lot* of USPS distribution centers, so it's very possible that the code is unable to accurately locate certain network distribution centers. However, the USPS events following an unfound network distribution center are typically in the same city, so the distance calculations should still be relatively accurate.
* The Google Maps option of the calculateMiles function will eventually get blocked by Google if you attempt too many calls.
* I have excluded APO deliveries for ease of implementation but can add it in if that is a highly requested feature.

## Contributions
CrowPy was created as an open-source project with the intention of steadily improving through improvements suggested by its users. The most obvious areas for contribution/improvement are: 
* the heuristic for deciding whether certain portions of the USPS trip were completed by plane or truck
* portability to other delivery services (UPS, FedEx, etc.)
* a suggestion for a third-party that is able to verify the accuracy of these functions

I have no authority on/prior experience with this, so I'm more than happy to collaborate on this project with more knowledgeable people. Constructive criticism is welcome :) If anyone has questions/suggestions for ways to improve the code, please contact me [here](https://jcapili.wixsite.com/jasoncapili/contact).