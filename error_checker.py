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
import pathlib

print(datetime.datetime.now())
cal = get_calendar('USFederalHolidayCalendar')  # Create calendar instance
cal.rules.pop(7)                                # Remove Veteran's Day rule
cal.rules.pop(6)                                # Remove Columbus Day rule
tradingCal = HolidayCalendarFactory('TradingCalendar', cal, GoodFriday)

# Set clean_dup(licates) to True to produce a cleaned file
def trading_periods(clean_dup=False, file_path=pathlib.Path('Data',
                                               'VXX_5MIN.tsv'), num=5):
    t0 = datetime.datetime.now()
    #--------- Load Data File ------------
    col_names = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']

    # GNF_df is used to store the historic data
    GNF_df = pd.read_table(file_path, index_col=0, names=col_names)
    GNF_df.index = pd.to_datetime(GNF_df.index)
    print('File Path\t: %s' % file_path)
    start_date = GNF_df.index[0] # First date
    end_date = GNF_df.index[-1]  # Last date

    print('Trading Periods\t: %s - %s' % (start_date, end_date))
    start_time = GNF_df.index[0].time() # Set the expected first period
    custom_index = get_custom_index(start_date, end_date, '5min')
    end_time = custom_index[-1].time()

    #--- Capture both missing and extra data ponts---
    missing_periods = custom_index.difference(GNF_df.index)
    extra_periods = GNF_df.index.difference(custom_index)
    first_period = []
    last_period = []

    # search through missing_periods to find missing days
    # assumes if missing first and last period it is a missing day
    # contains a the pd.DateTime of the starting period
    for period in missing_periods:
        if period.time() == start_time:
            first_period.append(period.date())
        # should end_time be either ending time for missing half days?
        elif period.time() == end_time:
            last_period.append(period.date())

    missing_days = [x for x in first_period if x in last_period]

    # find duplicates timestamps; write to file if clean_dup
    if not GNF_df.index.is_unique:
        print('\nDuplicate periods %s' % len(GNF_df[GNF_df.index.duplicated()]))
        first = pd.unique(GNF_df.index[GNF_df.index.duplicated()].date)[0]
        last = pd.unique(GNF_df.index[GNF_df.index.duplicated()].date)[-1]
        print('Start\t %s \nEnd\t %' % (first, last))
        if clean_dup:
            GNF_df[~GNF_df.index.duplicated()].to_csv('cleaned.tsv', sep='\t',
                                                  header=False)
    print('\nMissing Days')
    for date in missing_days:
        print(date)

    # Remove missing days from first_period and last_period
    first_period = [x for x in first_period if x not in missing_days]
    last_period = [x for x in last_period if x not in missing_days]

    # Incorrect Trading Hours
    print('\nIncorrect Trading Hours')
    for period in first_period[:num]:
        start = GNF_df[period.strftime("%Y-%m-%d")].index[0]
        print('Start %s' % start)
    if len(first_period) > num:
        print('First %s of %s' % (num, len(first_period)))
    for period in last_period[:num]:
        end = GNF_df[period.strftime("%Y-%m-%d")].index[-1]
        print('End %s' % end)
    if len(last_period) > num:
        print('First %s of %s' % (num, last_period))

    # Extra periods
    days_with_extra_periods = pd.unique(extra_periods.date)
    print('\nExtra periods')
    for day in days_with_extra_periods[:num]:
        first_time = extra_periods[extra_periods.date == day][0].time()
        last_time = extra_periods[extra_periods.date == day][-1].time()
        print('%s Begin %s End %s' % (day, first_time, last_time))
    if len(days_with_extra_periods) > num:
        print('First %s of %s' % (num, len(days_with_extra_periods)))
    print('\nTime elasped %s' % (datetime.datetime.now() - t0))

def get_custom_index(start_date, end_date, frequency):
    """
    Makes a custom index of pandas timestamps based on the trading hours of
    the NYSE

    start_date: pd.Timestamp object on which to start the index
    end_date: pd.Timestamp object on which to end the index
    frequency: a pandas frequency str (e.g., '5min') that should be evenly divisible
          by 390min (full day) and 210min (half day)
    """
    custom_index = pd.date_range(start_date, end_date, freq='B')#.map(times)
    # start_time= pd.Timestamp(start_date.year, start_date.month, start_date.day, 9, 30)
    start_time = start_date.time()

    #-------- Holidays-----------
    cal1 = tradingCal()    # new instance of class
    holidays = cal1.holidays(start_date, end_date)

    # When New Years day is on a Saturday NYE is not a holiday for NYSE
    # Is this condition already checked?
    nye = holidays[(holidays.month == 12) & (holidays.day == 31)]
    holidays = holidays.drop(nye)

    # Half days
    # Thanksgiving
    half_days = (holidays[holidays.month == 11] +
                     datetime.timedelta(days=1))
    # July 4th
    half_days = half_days.append((holidays[(holidays.month == 7) & (
        holidays.day == 4)] - datetime.timedelta(days=1)))

    # Christmas Eve
    xmas_eve=[]
    for year in pd.unique(holidays.year):
        xmas_eve.append(datetime.date(year, 12, 24))
    half_days = half_days.append(pd.DatetimeIndex(xmas_eve)).sort_values()
    #-------------------------
    datetimes = []
    for date in custom_index:
        if date.date() in holidays:
            continue
        elif date.date() in half_days:
            datetimes.append(pd.date_range(date.strftime("%Y-%m-%d")+' '+
                                str(start_time), periods=42, freq='5min'))
        else:
            datetimes.append(pd.date_range(date.strftime("%Y-%m-%d")+' '+
                                str(start_time), periods=78, freq='5min'))
    custom_index = pd.to_datetime(np.concatenate(datetimes))
    return custom_index

if __name__ == '__main__':
    if len(sys.argv) == 1:
        trading_periods()
    elif len(sys.argv) == 2:
        trading_periods(file_path=sys.argv[1])
    elif len(sys.argv) == 3:
        trading_periods(file_path=sys.argv[1], num=int(sys.argv[2]))
    else:
        print('Script takes no more than two args: data_file_path num_errors_to_print')
