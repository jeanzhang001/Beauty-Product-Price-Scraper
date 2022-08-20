import requests
from glob import glob
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from time import sleep
import csv
import smtplib
from email.mime.multipart import MIMEMultipart

HEADERS = {'user-agent':
           'Mozilla/5.0 (Macintosh; Intel Mac OS Monterey 12_0_1) \
           AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15'}

def search_product_list(interval_count = 1, interval_hours = 6):
    """
    This function lods a csv file named TRACKER_PRODUCTS.csv, with headers: [url, code, buy_below]
    It looks for the file under in ./trackers
    
    It also requires a file called SEARCH_HISTORY.xslx under the folder ./search_history to start saving the results.
    An empty file can be used on the first time using the script.
    
    Both the old and the new results are then saved in a new file named SEARCH_HISTORY_{datetime}.xlsx
    This is the file the script will use to get the history next time it runs.

    Parameters
    ----------
    interval_count : TYPE, optional
        DESCRIPTION. The default is 1. The number of iterations you want the script to run a search on the full list.
    interval_hours : TYPE, optional
        DESCRIPTION. The default is 6.

    Returns
    -------
    New .xlsx file with previous search history and results from current search

    """
    beauty_tracker = pd.read_csv('trackers/BEAUTY_PRODUCT.csv', sep=',', quoting=csv.QUOTE_NONE, encoding='utf-8')
    beauty_tracker_URLS = beauty_tracker.url
    tracker_log = pd.DataFrame()
    now = datetime.now().strftime('%Y-%m-%d %Hh%Mm')
    interval = 0 # counter reset
    
    while interval < interval_count:

        for x, url in enumerate(beauty_tracker_URLS):
            page = requests.get(url, headers=HEADERS)
            soup = BeautifulSoup(page.content, features="html.parser")
            
            #product title
            title = soup.find('div',{'class':"ProductMainSection__productName"}).get_text().strip()
            
            # to prevent script from crashing when there isn't a price for the product
            try:
                price = float(soup.find('div',{'class':"ProductPricingPanel"}).get_text().replace('Price', '').replace('$', ''))
            except:
                price = ''


            log = pd.DataFrame({'date': now.replace('h',':').replace('m',''),
                                'code': beauty_tracker.code[x], # this code comes from the BEAUTY_PRODUCT file
                                'url': url,
                                'title': title,
                                'buy_below': beauty_tracker.buy_below[x], # this price comes from the BEAUTY_PRODUCT file
                                'price': price}, index=[x])

            try:
                if price < beauty_tracker.buy_below[x]:
                    print('************************ ALERT! Buy the '+ beauty_tracker.code[x]+' ************************')
                    
                    username = '' # Put your hotmail address inside ''
                    password = ''  # Put your password inside ''

                    server = smtplib.SMTP('smtp.outlook.com', 587)
                    server.ehlo()
                    server.starttls()
                    server.login(username, password)
                    msg = ('Subject: Beauty Price Alert\n\n\
                    Product: {}\nNew Price: {}\n\nOld Price: {}\n\nEnd of message'.format(beauty_tracker.code[x], price, beauty_tracker.buy_below[x]))
                    message = MIMEMultipart()
                    message['From'] = '' # Putyour hotmail address inside ''
                    message['to'] = '' # Put your other email address inside ''
                    server.sendmail('', '', msg) # put your hotmail address inside the first '', and the other email address inside the second ''
                    print('sent email.....')
            except:
                # sometimes we don't get any price, so there will be an error in the if condition above
                pass

            tracker_log = tracker_log.append(log)
            print('appended '+ beauty_tracker.code[x] +'\n' + title + '\n\n')            
            sleep(5)
        
        interval += 1# counter update
        
        sleep(interval_hours*1*1)
        print('end of interval '+ str(interval))
    
    # after the run, checks last search history record, and appends this run results to it, saving a new file
    last_search = glob('python_project/search_history/*.xlsx')[-1] # path to file in the folder
    search_hist = pd.read_excel(last_search)
    final_df = search_hist.append(tracker_log, sort=False)
    
    final_df.to_excel('python_project/search_history/SEARCH_HISTORY_{}.xlsx'.format(now), index=False)
    print('end of search')

search_product_list()