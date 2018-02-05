# -*- coding: utf-8 -*-
"""
Created on Sat Jul 22 13:11:30 2017
-----------------Trading Period Error Checker v0.1-----------------------------
                    Last updated 31st August 2017
-------------------------------------------------------------------------------
Script for checking trading periods for historical ohlc files. Currently 
assumes 5 minute tick data and that the first period is the correct starting 
time of the trading day. Can be used either from command line or jupyter 
notebook. Checks for duplicated, missing and extra trading periods. Option to 
create a cleaned.tsv file with duplicates removed. In doing so assumes the first
occurrence is correct.

From command line:
$python error_checker.py [filename] [num of errors to return]
Where filename is either full path or subdirectory/filename.extension

In jupyter: 
from error_checker import trading_periods
trading_periods(file_path='[filename]')

Features for next realease : Estimate the first period of the day instead of 
assuming first period is correct. 
-------------------------------------------------------------------------------
"""
import sys
import pandas as pd
import numpy as np
from pandas.tseries.holiday import (get_calendar, HolidayCalendarFactory,
                                    GoodFriday)
import datetime

print(datetime.datetime.now())
cal = get_calendar('USFederalHolidayCalendar')  # Create calendar instance
cal.rules.pop(7)                                # Remove Veteran's Day rule
cal.rules.pop(6)                                # Remove Columbus Day rule
tradingCal = HolidayCalendarFactory('TradingCalendar', cal, GoodFriday)

# Current version
def trading_periods(clean_dup=False, file_path='Data\\VXX_5MIN.tsv', num=5):
    t0=datetime.datetime.now()
    #--------- Load Data File ------------
    col_names=['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    GNF_df=pd.read_table(file_path, index_col=0, names=col_names)
    GNF_df.index=pd.to_datetime(GNF_df.index)
    print('File Path\t:', file_path)
    start_date=GNF_df.index[0]
    end_date=GNF_df.index[-1]
    print('Trading Periods\t:',start_date,'-',end_date)
    start_time=GNF_df.index[0].time()
    
    #---- Make a custom index---
    index=pd.date_range(start_date, end_date, freq='B')#.map(times)

    #-------- Holidays-----------
    cal1 = tradingCal()    # new instance of class
    holidays=cal1.holidays(start_date, end_date)
    # When New Years day is on a Saturday NYE is not a holiday for NYSE 
    nye=holidays[(holidays.month == 12) & (holidays.day == 31)]
    holidays=holidays.drop(nye)

    # Half days
    # Thanksgiving
    half_days=(holidays[holidays.month == 11] +
                     datetime.timedelta(days=1))
    # July 4th
    half_days=half_days.append((holidays[(holidays.month == 7) & (
        holidays.day == 4)] - datetime.timedelta(days=1)))
    xmas_eve=[]
    for year in pd.unique(holidays.year):
        xmas_eve.append(datetime.date(year,12,24))
    half_days=half_days.append(pd.DatetimeIndex(xmas_eve)).sort_values()
    #-------------------------
    datetimes = []
    for date in index:
        if date.date() in holidays:
            continue
        elif date.date() in half_days:
            datetimes.append(pd.date_range(date.strftime("%Y-%m-%d")+' '+
                                str(start_time), periods=42, freq='5min'))
        else:
            datetimes.append(pd.date_range(date.strftime("%Y-%m-%d")+' '+
                                str(start_time), periods=78, freq='5min'))
    index=pd.to_datetime(np.concatenate(datetimes))
    end_time=index[-1].time()

    #--- Capture both missing and extra data ponts---
    missing_periods=index.difference(GNF_df.index)
    extra_periods=GNF_df.index.difference(index)
    first_period = []
    last_period = []
    for period in missing_periods:
        if period.time() == start_time:
            first_period.append(period.date())
        elif period.time() == end_time:
            last_period.append(period.date())

    missing=[x for x in first_period if x in last_period]
    if not GNF_df.index.is_unique:
        print('\nDuplicate periods', len(GNF_df[GNF_df.index.duplicated()]))
        first=pd.unique(GNF_df.index[GNF_df.index.duplicated()].date)[0]
        last=pd.unique(GNF_df.index[GNF_df.index.duplicated()].date)[-1]
        print('Start\t',first,'\nEnd\t',last)
        if clean_dup:
            GNF_df[~GNF_df.index.duplicated()].to_csv('cleaned.tsv',sep='\t',
                                                  header=False)
    print('\nMissing Days')
    for date in missing:
        print(date)
    # Remove missing days
    first_period=[x for x in first_period if x not in missing]
    last_period=[x for x in last_period if x not in missing]
    print('\nIncorrect Trading Hours')
    for period in first_period[:num]:
        start=GNF_df[period.strftime("%Y-%m-%d")].index[0]
        print('Start ',start)
    if len(first_period) > num:
        print('First',str(num),'of',str(len(first_period)))
    for period in last_period[:num]:
        end=GNF_df[period.strftime("%Y-%m-%d")].index[-1]
        print('End ',end)
    if len(last_period) > num:
        print('First',str(num),'of',str(len(last_period)))
    extra_days = pd.unique(extra_periods.date)
    print('\nExtra periods')
    for day in extra_days[:num]:
        first_time=extra_periods[extra_periods.date == day][0].time()
        last_time=extra_periods[extra_periods.date == day][-1].time()
        print(day, 'Begin',first_time, 'End', last_time)
    if len(extra_days) > num:
        print('First',str(num),'of',str(len(extra_days)))
    print('\nTime elasped ',datetime.datetime.now()-t0)    

if __name__ == '__main__':
    if len(sys.argv)==1:
        trading_periods()
    elif len(sys.argv)==2:
        trading_periods(file_path=sys.argv[1])
    elif len(sys.argv)==3:
        trading_periods(file_path=sys.argv[1],num=int(sys.argv[2]))