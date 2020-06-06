# CrowPy

CrowPy (pronounced "*crow-pie*") uses Python to calculate the number of plane and truck miles traveled to deliver a USPS package. The name is a pun on the phrase "As the crow flies."

CrowPy was created to allow developers at e-commerce companies to easily track how many aggregate miles their packages have traveled in order to offset the associated carbon emissions. 

# Installation

# Usage

# Accuracy

# Known Bugs
* There are a *lot* of USPS distribution centers, so it's very possible that the code is unable to accurately locate 
* The Google Maps option of the calculateMiles function will eventually get blocked by Google if you attempt too many calls.

# Contributions

CrowPy was created as an open-source project with the intention of steadily improving through improvements suggested by its users. The biggest areas for improvement are: \
* the heuristic for deciding whether certain portions of the USPS trip were completed by plane or truck
* portability to other delivery services (UPS, FedEx, etc.)\
If anyone has questions/suggestions for ways to improve the code, please contact me [here](https://jcapili.wixsite.com/jasoncapili/contact).