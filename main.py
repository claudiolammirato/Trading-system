from typing import no_type_check
import datetime
import numpy as np
import pandas as pd
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

def main():
    data = load_data_daily()
    enter_rules = crossover(data.close,data.hhv20.shift(1))
    exit_rules = crossunder(data.close,data.llv5.shift(1)) | crossunder(data.day,data.day.shift(1))

    print(enter_rules)
    print(enter_rules[enter_rules == True].count())
    print(exit_rules[exit_rules == True].count())
    

if __name__ == "__main__":
    main()

