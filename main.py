from typing import no_type_check
import datetime
import numpy as np
import pandas as pd
from pandas.core.frame import DataFrame
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib
import yfinance as yf

#library settings
matplotlib.use('TkAgg')
pd.options.display.max_rows = 99999



def load_data_daily():
    data  = yf.download('AAPL', start='2000-01-01', end='2021-10-01', progress=False,)
    data.columns = ["date", "open", "high", "low", "close", "volume"]
    data["dayofweek"] = data.index.dayofweek
    data["day"] = data.index.day
    data["month"] = data.index.month
    data["year"] = data.index.year
    data["dayofyear"] = data.index.dayofyear
    data["quarter"] = data.index.quarter
    data["hhv20"] = data.high.rolling(20).max()
    data["llv20"] = data.high.rolling(20).min()
    data["hhv5"] = data.high.rolling(20).max()
    data["llv5"] = data.high.rolling(20).min()
   
    return data
    
def crossover(array1,array2):
    return (array1>array2) & (array1.shift(1) < array2.shift(1))

def crossunder(array1,array2):
    return (array1<array2) & (array1.shift(1)> array2.shift(1))

def marketposition_generator(enter_rules, exit_rules):
    #Funzione per calcolare il marketposition date due serie di enter_rules e exit_rules
    service_dataframe = pd.DataFrame(index = enter_rules.index)
    service_dataframe['eneter_rules'] = enter_rules
    service_dataframe['exit_rules'] = exit_rules

    status = 0
    mp = []
    for (i,j) in zip(enter_rules,exit_rules):
        if status == 0:
            if i == 1 and j != -1:
                status = 1
        else:
            if j == -1:
                status = 0
        mp.append(status)
    
    service_dataframe['mp_new'] = mp
    service_dataframe.mp_new = service_dataframe.mp_new.shift(1)
    service_dataframe.iloc[0,2] = 0
    service_dataframe.to_csv('marketposition_generator.csv')
    return service_dataframe.mp_new

def apply_trading_system(imported_dataframe,direction,ORDER_TYPE,INSTRUMENT,OPERATION_MONEY, COSTS,enter_level,enter_rules,exit_rules):
    dataframe = imported_dataframe.copy()
    dataframe['enter_rules'] = enter_rules.apply(lambda x: 1 if x == True else 0)
    dataframe['exit_rules'] = exit_rules.apply(lambda x: -1 if x == True else 0)
    dataframe['mp'] = marketposition_generator(dataframe.enter_rules, dataframe.exit_rules)

    if ORDER_TYPE == 'market':
        dataframe["entry_price"] = np.where((dataframe.mp.shift(1) == 0) & (dataframe.mp == 1), dataframe.open, np.nan)

        if INSTRUMENT == 1:
            dataframe["number_of_stocks"] = np.where((dataframe.mp.shift(1) == 0) & (dataframe.mp == 1), OPERATION_MONEY / dataframe.open, np.nan)
    dataframe["entry_price"] = dataframe["entry_price"].fillna(method='ffill')
    if INSTRUMENT == 1:
        dataframe["number_of_stocks"] = dataframe["number_of_stocks"].apply(lambda x: round(x,0)).fillna(method='ffill')
    dataframe["events_in"] = np.where((dataframe.mp == 1) & (dataframe.mp.shift(1) == 0), "entry", "")

    if direction == "long":
        if INSTRUMENT == 1:
            dataframe["open_operations"] = (dataframe.close - dataframe.entry_price) * dataframe.number_of_stocks
            dataframe["open_operations"] = np.where((dataframe.mp == 1) & (dataframe.mp.shift(-1) == 0), (dataframe.open.shift(-1) - dataframe.entry_price)*dataframe.number_of_stocks - 2 * COSTS, dataframe.open_operations)
    else:
        if INSTRUMENT == 1:
            dataframe["open_operations"] = (dataframe.close - dataframe.close) * dataframe.number_of_stocks
            dataframe["open_operations"] = np.where((dataframe.mp == 1) & (dataframe.mp.shift(-1) == 0), (dataframe.entry_price - dataframe.open.shift(-1) )*dataframe.number_of_stocks - 2 * COSTS, dataframe.open_operations)
    
    dataframe["open_operations"] = np.where(dataframe.mp == 1, dataframe.open_operations,0)
    dataframe["events_out"] = np.where((dataframe.mp == 1) & (dataframe.exit_rules == -1), "exit","")
    dataframe["operations"] = np.where((dataframe.exit_rules == -1) & (dataframe.mp == 1), dataframe.open_operations, np.nan)
    dataframe["closed_equity"] = dataframe.operations.fillna(0).cumsum()
    dataframe["open_equity"] = dataframe.closed_equity + dataframe.open_operations - dataframe.operations.fillna(0)
    dataframe.to_csv("trading_system_export.csv")
    return dataframe

def main():
    data = load_data_daily()
    enter_rules = crossover(data.close,data.hhv20.shift(1))
    exit_rules = crossunder(data.close,data.llv5.shift(1)) | crossunder(data.day,data.day.shift(1))
    #print(enter_rules)
    #print(enter_rules[enter_rules == True].count())
    #print(exit_rules[exit_rules == -1].count())

    COSTS = 0
    INSTRUMENTS = 1 #1 equity/forex - 2 future
    OPERATION_MONEY = 10000
    DIRECTION = 'long'
    ORDER_TYPE = 'market'
    enter_level = data.open

    trading_system = apply_trading_system(data, DIRECTION, ORDER_TYPE, INSTRUMENTS,OPERATION_MONEY,COSTS, enter_level, enter_rules, exit_rules)
    #print(trading_system.iloc[500:600,15:])
    print(trading_system)

    

if __name__ == "__main__":
    main()

