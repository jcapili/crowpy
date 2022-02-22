from crowpy import *

cp = CrowPy('070SHIPP8017')
print(cp.calculateMiles('9405509206119500403250'))
cp.calculateCSVMiles('~/Downloads/shortTest.csv', '~/Downloads/shortTestResults.csv')