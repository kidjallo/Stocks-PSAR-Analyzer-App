# On Mac
# brew install python-tk
import os
import sys
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog as fd
import tkinter.ttk as ttk
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import yfinance as yf
# from psar import PSAR
import threading


from collections import deque

class PSAR:
    def __init__(self, init_af=0.02, max_af=0.2, af_step=0.02):
        self.max_af = max_af
        self.init_af = init_af
        self.af = init_af
        self.af_step = af_step
        self.extreme_point = None
        self.high_price_trend = []
        self.low_price_trend = []
        self.high_price_window = deque(maxlen=2)
        self.low_price_window = deque(maxlen=2)

    # Lists to track results
        self.psar_list = []
        self.af_list = []
        self.ep_list = []
        self.high_list = []
        self.low_list = []
        self.trend_list = []
        self._num_days = 0

    def calcPSAR(self, high, low):
        if self._num_days >= 3:
            
            # print("******************")
            psar = self._calcPSAR()
        else:
            # print("##################")
            psar = self._initPSARVals(high, low)

        psar = self._updateCurrentVals(psar, high, low)
        self._num_days += 1

        return psar


    def _initPSARVals(self, high, low):
        if len(self.low_price_window) <= 1:
            self.trend = None
            self.extreme_point = high
            return None

        if self.high_price_window[0] < self.high_price_window[1]:
            self.trend = 1
            psar = min(self.low_price_window)
            self.extreme_point = max(self.high_price_window)
        else: 
            self.trend = 0
            psar = max(self.high_price_window)
            self.extreme_point = min(self.low_price_window)
        return psar

    def _calcPSAR(self):
        prev_psar = self.psar_list[-1]
        if self.trend == 1: # Up
            psar = prev_psar + self.af * (self.extreme_point - prev_psar)
            psar = min(psar, min(self.low_price_window))
        else:
            psar = prev_psar - self.af * (prev_psar - self.extreme_point)
            psar = max(psar, max(self.high_price_window))

        return psar
    def _updateCurrentVals(self, psar, high, low):
        if self.trend == 1:
            self.high_price_trend.append(high)
        elif self.trend == 0:
            self.low_price_trend.append(low)

        psar = self._trendReversal(psar, high, low)

        self.psar_list.append(psar)
        self.af_list.append(self.af)
        self.ep_list.append(self.extreme_point)
        self.high_list.append(high)
        self.low_list.append(low)
        self.high_price_window.append(high)
        self.low_price_window.append(low)
        self.trend_list.append(self.trend)

        return psar

    def _trendReversal(self, psar, high, low):
        reversal = False
        if self.trend == 1 and psar > low:
            self.trend = 0
            psar = max(self.high_price_trend)
            self.extreme_point = low
            reversal = True
        elif self.trend == 0 and psar < high:
            self.trend = 1
            psar = min(self.low_price_trend)
            self.extreme_point = high
            reversal = True

        if reversal:
            self.af = self.init_af
            self.high_price_trend.clear()
            self.low_price_trend.clear()
        else:
            if high > self.extreme_point and self.trend == 1:
                self.af = min(self.af + self.af_step, self.max_af)
                self.extreme_point = high
            elif low < self.extreme_point and self.trend == 0:
                self.af = min(self.af + self.af_step, self.max_af)
                self.extreme_point = low

        return psar

class MigrationApp(object):

    def __init__(self):
        super(MigrationApp, self).__init__()
        self.root = tk.Tk()
        self.root.title("Algo-Trading PSAR")
        # make the window 1200x600 and place it at (50,50)
        self.root.geometry("600x600")
        #self.root.config(bg="blue")
        self.make_box()
        
        
    def make_box(self):
        # Create a frame for the graphs
        self.graph_frame = tk.Frame(self.root)
        self.graph_frame.pack(pady=10)
        
        # Create buttons to display the graphs
        self.graph1_button = tk.Button(self.graph_frame, text="Start", command=threading.Thread(target=self.get_psar_value).start)
        self.graph1_button.grid(row=0, column=0, padx=10)
        
        # create a progress bar
        self.progress = tk.IntVar()
        self.progress.set(0)
        self.progress_bar = tk.ttk.Progressbar(self.graph_frame, variable=self.progress, maximum=100)
        self.progress_bar.grid(row=1, column=0, padx=10, pady=30, ipadx=100, ipady=7)
        
        
    def get_psar_value(self):
        
        # add a text box under the progress bar Please Wait Calculating values ...
        self.text_box = tk.Text(self.graph_frame, height=2, width=30)
        self.text_box.grid(row=2, column=0, padx=10, pady=10)
        self.text_box.insert(tk.END, "Please Wait Calculating values ...")
        
        
        start_date='2020-01-01'
        df = pd.read_csv(r"listedtest.csv")
        # Create an empty list to store data
        data_list = []
        today_date = datetime.date.today()
        symbols = df['Symbol']
        end_date = datetime.date.today()
        
        total_val = 10
        
        # set the maximum value of progress bar
        self.progress_bar['maximum'] = len (symbols)
        cur_val = 0

        today_date = datetime.date.today()
        for i in symbols:
            try:
                ticker = i
                yfObj = yf.Ticker(ticker)
                data = yfObj.history(start='2020-01-01', end=today_date)
                indic = PSAR()

                psar_values = []  # Create a list to store PSAR values

                for index, row in data.iterrows():
                    psar_value = indic.calcPSAR(row['High'], row['Low'])
                    psar_values.append(psar_value)
                    
                # add the value of progress bar
                cur_val += 1
                self.progress.set(cur_val)

                # Append the PSAR value to the list along with the symbol
                data_list.append({'Symbol': i, 'PSAR Value': psar_values[-1]})

            except IndexError:
                cur_val += 1
                self.progress.set(cur_val)
                pass
                
        # rerender the progress bar
        self.root.update_idletasks()
        
        if not os.path.exists(f"{end_date}"):
            os.mkdir(f"{end_date}")
            
        df = pd.DataFrame(data_list)
            
        top_5 = df.nlargest(5, 'PSAR Value')
        # print(top_5)

        #get percentage gain/loss for top 5 values
        # for index, row in top_5.iterrows():
        #     ticker = row['Symbol']
        #     percentage_change = self.calculate_percentage_gain_loss(ticker, start_date, end_date)
        #     print(f"{ticker}: {percentage_change}")
        #     #save percentage change of top 5 in a new data frame with ticker
        #     top_5['Percentage Change'] = percentage_change

        # #save top 5 in a csv file
        # top_5.to_csv(f"{end_date}/top_5.csv")
        
        # create a columns 

        #plot top 5 with psar
        for index, row in top_5.iterrows():
            ticker = row['Symbol']
            percentage_change = self.calculate_percentage_gain_loss(ticker, start_date, end_date)
            top_5.at[index, 'Percentage Change'] = percentage_change
            yf.pdr_override()
            today_date = datetime.date.today()
            yfObj = yf.Ticker(ticker)
            data = yfObj.history(start='2020-01-01', end=today_date)
            # Calculate PSAR values
            indic = PSAR()
            for index, row in data.iterrows():
                psar_value = indic.calcPSAR(row['High'], row['Low'])
                data.at[index, 'PSAR'] = psar_value
            data['EP'] = indic.ep_list
            data['Trend'] = indic.trend_list
            data['AF'] = indic.af_list

            # Create plots
            colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
            # Plot 1: Price and PSA
            psar_bull = data.loc[data['Trend'] == 1]['PSAR']
            psar_bear = data.loc[data['Trend'] == 0]['PSAR']
            
            # now make a figure and save it
            fig = plt.figure(figsize=(20, 20))
            ax = fig.add_subplot(111)
            ax.plot(data['Close'], label='Close', linewidth=1)
            ax.scatter(psar_bull.index, psar_bull, color=colors[1], label='Up Trend', s=50)
            ax.scatter(psar_bear.index, psar_bear, color=colors[3], label='Down Trend', s=50)
            # add x and y labels and title
            ax.set_xlabel('Date')
            ax.set_ylabel('Price ($)')
            ax.set_title(f'{ticker} Price and Parabolic SAR')
            # add text box with percentage change
            ax.text(0.05, 0.95, f"Percentage Change: {percentage_change}", transform=ax.transAxes, fontsize=14,
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.5))
            
            
            # save the figure
            fig.savefig(f"{end_date}/{ticker}_price_and_psar.png")
            
            
            buy_sigs = data.loc[data['Trend'].diff() == 1]['Close']
            short_sigs = data.loc[data['Trend'].diff() == -1]['Close']
            
            fig2 = plt.figure(figsize=(20, 20))
            ax2 = fig2.add_subplot(111)
            ax2.plot(data['Close'], label='Close', linewidth=1, zorder=0)
            ax2.scatter(buy_sigs.index, buy_sigs, color=colors[2], label='Buy', marker='^', s=100)
            ax2.scatter(short_sigs.index, short_sigs, color=colors[4], label='Short', marker='v', s=100)
            ax2.set_xlabel('Date')
            ax2.set_ylabel('Price ($)')
            ax2.set_title(f'{ticker} Price and Parabolic SAR')
            
            ax2.text(0.05, 0.95, f"Percentage Change: {percentage_change}", transform=ax.transAxes, fontsize=14,
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.5))
            
            fig2.savefig(f"{end_date}/{ticker}_buy_and_short_signals.png")
            
            
        top_5.to_csv(f"{end_date}/top_5.csv")
        # change the text to Done
        # self.text_box.delete(1.0, tk.END)
        # self.text_box.insert(tk.END, "Done")
        
        print (data_list)
        
    def calculate_percentage_gain_loss(self, ticker, start_date, end_date):
        # Download historical data
        
        print ("Symbol is = ", ticker)
        yfObj = yf.Ticker(ticker)
        data = yfObj.history(start=start_date, end=end_date)
        
        # Create an instance of the PSAR class
        indic = PSAR()
        
        # Initialize variables for tracking trades
        holding = False
        buy_price = 0.0
        percentage_changes = []
        
        # Iterate through historical data
        for index, row in data.iterrows():
            psar_value = indic.calcPSAR(row['High'], row['Low'])
            
            # Check if psar_value is None
            if psar_value is not None:
                # Buy condition
                if row['Close'] > psar_value and not holding:
                    holding = True
                    buy_price = row['Close']
                
                # Sell condition
                elif row['Close'] < psar_value and holding:
                    holding = False
                    sell_price = row['Close']
                    percentage_change = ((sell_price - buy_price) / buy_price) * 100.0
                    percentage_changes.append(percentage_change)
        
        # Calculate the overall percentage gain or loss
        if len(percentage_changes) > 0:
            total_percentage_change = sum(percentage_changes)
        else:
            total_percentage_change = 0.0
        
        return total_percentage_change
        
    def start(self):
        self.root.mainloop()
        
    
   
#--------------------------------------
#           Main Function
#--------------------------------------
def main():
    app = MigrationApp()
    app.start()

if __name__ == '__main__':
    main()

