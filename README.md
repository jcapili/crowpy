# CrowPy
CrowPy (pronounced "*crow-pie*") uses Python to calculate the number of plane and truck miles traveled to deliver a USPS package. The name is a pun on the phrase "As the crow flies."

CrowPy was created to allow companies to easily track how many aggregate miles their packages have traveled in order to offset the associated carbon emissions. 

# Installation

# Usage

# Accuracy
There is no third-party entity I know of that can be used to verify the accuracy of these functions. That being said, these functions have been tested and spot checked using Google Maps, which is probably the foremost tool for verifying the accuracy. The plane miles are calculated using Geopy's API, and they should be relatively accurate given the direct nature of plane travel.

The most likely point of inaccuracy is calculating driving distance, which is often very different from the distance as the crow flies (hence the name of this project). So the driving miles are calculated based on the 1.417 detour index from [this](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3835347/) national study, where the detour index defined as travel distance divided by straight-line distance. The "google" boolean flag in the `calculateMiles` function will provide links to Google Maps routes that can be used to spot check the accuracy of this detour index on a case-by-case basis. But based on past tests, the detour index calculations are typically an overestimate of the Google Maps calculations, which often is preferred so that you can be relatively confident you're *totally* offsetting all shipping-related emissions.

# Known Bugs
* There are a *lot* of USPS distribution centers, so it's very possible that the code is unable to accurately locate certain network distribution centers. However, the USPS events following an unfound network distribution center are typically in the same city, so the distance calculations should still be relatively accurate.
* The Google Maps option of the calculateMiles function will eventually get blocked by Google if you attempt too many calls.
* I have excluded APO deliveries for ease of implementation but can add it in if that is a highly requested feature.

# Contributions
CrowPy was created as an open-source project with the intention of steadily improving through improvements suggested by its users. The most obvious areas for contribution are: 
* the heuristic for deciding whether certain portions of the USPS trip were completed by plane or truck
* portability to other delivery services (UPS, FedEx, etc.)
* a suggestion for a third-party that is able to verify the accuracy of these functions

I have no authority on/prior experience with this, so I'm more than happy to collaborate on this project with more knowledgeable people -- in fact, constructive criticism is encouraged because that's the whole reason for this online release. If anyone has questions/suggestions for ways to improve the code, please contact me [here](https://jcapili.wixsite.com/jasoncapili/contact).