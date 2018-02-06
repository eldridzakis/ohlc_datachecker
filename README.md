# Market Data Error Checker
Commonly with historical pricing data, there are missing periods or extra periods outside of trading hours. This script can be run to both 
find missing trading periods; either enitre days or individual periods, and extra trading periods.

## -----------------Trading Period Error Checker v0.1-----------------------------<br>
*Last updated 31st August 2017* <br>
Script for checking trading periods for historical ohlc files. Currently 
assumes 5 minute tick data and that the first period is the correct starting 
time of the trading day. Can be used either from command line or jupyter 
notebook. Checks for duplicated, missing and extra trading periods. Option to 
create a cleaned.tsv file with duplicates removed. In doing so assumes the first
occurrence (trading period) is correct (the desired first period for each subsequent day).

## Inputs
Historical pricing data in tsv format

## Output
Prints the errors

## Usage
*From command line:*
```
$python error_checker.py [filename] [number of errors to return]
```
Where filename is either full path or subdirectory/filename.extension

*In jupyter:*
```
from error_checker import trading_periods
trading_periods(file_path='[filename]')
```
Features for next realease : Estimate the first period of the day instead of assuming first period is correct. 
