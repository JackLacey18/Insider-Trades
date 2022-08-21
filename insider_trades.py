if __name__ == ('__main__'):
	# FUNCTION TO FETCH STOCK DATA FOR THE LAST 5 YEARS FOR A PARTICULAR STOCK
	def stock_grab(ticker):
	    import requests
	    import os
	    from datetime import datetime
	    from datetime import timedelta
	    from datetime import date
	    import time  
	    z = 0
	    date_today = date.today()
	    date_today = date_today - timedelta(days = z)
	    date_month = date_today - timedelta(days = z + 1825)
	    today_format = date_today.strftime("%Y/%m/%d")
	    month_format = date_month.strftime("%Y/%m/%d")
	    from_date = str(month_format)
	    to_date = str(today_format)
	    from_datetime = datetime.strptime(from_date,'%Y/%m/%d')
	    to_datetime = datetime.strptime(to_date,'%Y/%m/%d')
	    from_epoch = int(time.mktime(from_datetime.timetuple()))
	    to_epoch = int(time.mktime(to_datetime.timetuple()))
	    url = 'https://query1.finance.yahoo.com/v7/finance/download/{}?period1={}&period2={}&interval=1d&events=history&includeAdjustedClose=true'.format(ticker,from_epoch,to_epoch)
	    #this will trick the website to think it is not a bot
	    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36"} 
	    content = requests.get(url,headers=headers).content
	    filename = 'Stock_Sheets\\' + ticker.upper() + '.csv'
	    with open(filename,'wb') as file:
	        file.write(content)
	    with open(filename,'r') as read_file:
	        file = read_file.readlines()
	    if file == ['404 Not Found: No data found, symbol may be delisted']:
	        if os.path.exists(filename):
	            os.remove(filename)
	            return 'Ticker not Found'
	    if file != ['404 Not Found: No data found, symbol may be delisted']:
	        return filename

	import bs4
	import requests
	import concurrent.futures
	from tqdm import tqdm
	import csv
	import pandas as pd
	import time
	import os
	# OPENING A FILE CONTAINING UNIQUE TICKERS FOR THE STOCKS WE WILL GATHER DATA FOR
	with open('stock_tickers.txt','r') as file:
	    tickers = [i.strip() for i in file.readlines()]
	# IF THE STOCK DATA FILE DOESN'T ALREADY EXIST FETCH IT
	for i in tickers:
	    path = 'Stock_Sheets\\{}.csv'.format(i)
	    if os.path.exists(path) == False:
	        stock_grab(i)
	# FUNCTION FOR FETCHING ALL RECORDS OF INSIDER TRADES FOR A PARTICULAR STOCK
	def insiderTrading(ticker):
	    try:
	        rows = []
	        base_url = 'http://openinsider.com/search?q={}'.format(ticker)
	        res = requests.get(base_url)
	        soup = bs4.BeautifulSoup(res.text,'html5lib' )
	        change = soup.find_all('td')
	        rawData = [i.text.strip() for i in change]
	        companyName = soup.find_all('h1')
	        h1Finder = soup.find_all('h1')
	        companyName = h1Finder[0].text.split(' - ')[1]
	        indexStart = rawData.index('6m')
	        indexEnd = rawData.index('Amended filing')
	        newData = rawData[indexStart+1:indexEnd-1]
	        indexes = []
	        for i in range(0,int(len(newData)/16)+1):
	            indexes.append(i*16)
	        for i in indexes[0:-1]:
	            rows.append(newData[i:i+16])
	        for i in rows:
	            i.append(companyName)
	        return rows
	    except:
	        pass
	# RUN THE INSIDER TRADING FUNCTION WITH CONCURRENT FUTURES TO NOT WASTE TIME WAITING FOR RESPONSES       
	with concurrent.futures.ThreadPoolExecutor(max_workers=32) as executor:
	    method = tqdm(executor.map(insiderTrading, tickers))
	    records = [i for i in method]
	joinedList = []
	for i in records:
	    if i != None:
	        for j in i:
	            joinedList.append(j)

	# JOINING DATA AND REMOVING COMMAS
	structuredData = []
	for i in joinedList:
	    tempList = []
	    tempList.append(''.join(i[-1].split(',')))
	    for j in i[1:12]:
	        tempList.append(str(''.join(str(''.join(j.split(','))).split('$'))))
	    structuredData.append(tempList)

	# APPENDING OPEN AND CLOSE PRICES FOR EACH STOCK FOR FILING DATE AND ACTIONED DATE
	for element in tqdm(structuredData):
	    ticker = element[3]
	    dateFiled = element[1].split(' ')[0]
	    dateTraded = element[2]
	    try:
	        dataframe = pd.read_csv('Stock_Sheets\\{}.csv'.format(ticker))
	    except:
	        try:
	            stock_grab(ticker)
	        except:
	            print(ticker)
	    try:
	        dataframe = pd.read_csv('Stock_Sheets\\{}.csv'.format(ticker))
	        date = dataframe[dataframe['Date'] == '{}'.format(dateFiled)]
	        atOpen = date.iloc[0, 1]
	        atClose = date.iloc[0, 4]
	        element.append(atOpen)
	        element.append(atClose)
	    except:
	        element.append('0')
	        element.append('0')
	    try:
	        date = dataframe[dataframe['Date'] == '{}'.format(dateTraded)]
	        atOpen = date.iloc[0, 1]
	        atClose = date.iloc[0, 4]
	        element.append(atOpen)
	        element.append(atClose)
	    except:
	        element.append('0')
	        element.append('0')
	        
	header = ['Company','Filing Date','Trade Date','Ticker','Insider Name','Title','Transaction Type','Price','Quantity',
	         'Owned','Change of Amount Owned','Value','Date Filed Open','Date Filed Close','Date Traded Open','Date Traded Close']

	with open('Insider_Trading.csv','w', encoding='UTF8', newline='') as file:
	        writer = csv.writer(file)
	        # write the header
	        writer.writerow(header)
	        # write multiple rows
	        writer.writerows(structuredData)