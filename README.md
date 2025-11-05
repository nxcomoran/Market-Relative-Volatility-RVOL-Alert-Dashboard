# Market-Relative-Volatility-RVOL-Alert-Dashboard

# 📊 Intraday RVOL Scanner

A **real-time Relative Volume (RVOL) scanning tool** built in **Python** with a **Tkinter GUI**, designed to monitor market tickers and identify unusually high-volume trading activity throughout the trading day.  
This project uses **Yahoo Finance’s API (via yfinance)** to fetch live intraday data, calculate RVOL across timeframes, and present results interactively through a responsive user interface.

---

## 🚀 Features

- **Live Scanning Mode** — Continuously scans a list of tickers in real time, flagging those with abnormal intraday volume activity.  
- **Test Mode** — Backtests historical data by scanning a specific timestamp and date to validate performance.  
- **Dynamic Thresholding** — User-adjustable RVOL threshold to control scan sensitivity.  
- **Custom Timeframes** — Supports minute-level resolution (`1m`, `2m`, `5m`, `15m`, etc.).  
- **Threaded Execution** — Runs scans on a background thread for smooth GUI responsiveness.  
- **Progress Tracking** — Displays scan progress and ticker-level feedback with a real-time progress bar.  
- **Debug Console** — Integrated log feed for runtime transparency and debugging.  
- **Pause / Resume** — Toggle scanning state without losing session context.  

---

## ⚙️ How It Works

The **RVOL (Relative Volume)** metric compares a ticker’s *current intraday volume* to its *average volume at the same time over previous days*:

Tickers exceeding a chosen threshold (default = 2.0×) are flagged as **high-activity securities**, potentially indicating institutional interest, volatility spikes, or news-driven movement.

---

## 🧠 Tech Stack

| Component | Description |
|------------|-------------|
| **Language** | Python 3.10+ |
| **Libraries** | `tkinter`, `yfinance`, `pandas`, `numpy`, `threading`, `queue` |
| **Data Source** | Yahoo Finance (via `yfinance`) |
| **Visualization / UI** | Tkinter (with live logs, text panels, and progress bar) |

---

## 📂 File Setup

You’ll need a list of tickers to scan, stored as a `.csv` file (one ticker per line):

```text
AAPL
MSFT
GOOG
TSLA
NVDA
AMZN
````

Set the correct file path in the code:

```python
ticker_file_path = 'D:/Python/Russell3000Holdings.csv'
```

---

## ▶️ Run the Application

### **1. Install Dependencies**

```bash
pip install yfinance pandas numpy
```

### **2. Run the Script**

```bash
python rvol_scanner.py
```

The GUI will launch automatically.

---

## 🖥️ GUI Overview

| Section               | Function                                    |
| --------------------- | ------------------------------------------- |
| **Scan Controls**     | Adjust RVOL threshold and select timeframe  |
| **Test Mode**         | Enter historical date/time for backtesting  |
| **Live Scan Buttons** | Start, stop, or pause live scanning         |
| **Results Panel**     | Displays tickers exceeding RVOL threshold   |
| **Debug Log**         | Shows system messages, errors, and progress |
| **Progress Bar**      | Indicates scan completion percentage        |

---

## 🧩 Example Output

```
Scanning: NVDA (42/3000)
[NVDA] MEETS CRITERIA! RVOL is 2.45
NVDA: RVOL = 2.45 (Vol: 1,230,000, Avg Vol: 503,000)
Scan complete. Waiting for next 5m candle...
```

---

## 💡 Key Concepts Demonstrated

* **Thread-safe GUI updates using queues**
* **Asynchronous data fetching with yfinance**
* **Real-time data analytics visualization**
* **Practical application of RVOL for market scanning**

---

## 🔧 Future Enhancements

* Integrate **watchlists** and **alert notifications**
* Add **matplotlib charts** for volume trend visualization
* Support **web dashboard export** (via Streamlit)
* Add **multi-threaded batch fetching** for faster scans

---

## 👤 Author

**Nico Moran**
📈 Quantitative Finance & Data Analytics
📧 [nxcomoran@gmail.com](mailto:nxcomoran@gmail.com)
🗓️ 2025

---

## 📜 License

Released under the **MIT License** — free for educational and analytical use.
