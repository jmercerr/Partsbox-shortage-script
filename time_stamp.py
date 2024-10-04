"""
Module that contains functions for dealing with timestamps 

"""

from datetime import datetime, timedelta


"""
Calculates Timestamps 
@params
    - none 
@returns 
    - Timestamps: dictionary of timestamps for the four time periods used and the current timestamp
                  timestamps are unix timestamps, in milliseconds represented as integers 
"""
def get_timestamps():
    Timestamps = {}
    num_months = (1, 3, 6, 12) #set number of months needed as a tuple 

    current_date = datetime.now()
    current_timestamp = int(current_date.timestamp())
    current_timestamp = current_timestamp * 1000 #convert to milliseconds
    Timestamps[0] = current_timestamp

    #get time stamps for 1 month ago, 3 months ago, 6 months ago, and 1 year ago
    for num in num_months: 
        difference = current_date.month - num

        #if in previous year
        if difference <= 0: 
            month = 12 + difference
            previous_date = current_date.replace(month=month, year=current_date.year-1)

        #if in the current year
        else:
            month = current_date.month - num
            previous_date = current_date.replace(month=month)

        #get timestamp as an int and store in dictionary of timestamps 
        previous_timestamp = int(previous_date.timestamp())
        previous_timestamp = previous_timestamp * 1000 #convert to milliseconds
        Timestamps[num] = previous_timestamp

    return Timestamps 


'''
calculates the difference in days between two timestamps 
@params
    - timestamp_1: first time stamp 
    - timestamp_2: second time stamp 
@returns 
    - difference: difference between two timestamps in days 
'''
def get_difference(timestamp_1, timestamp_2):
    MILLI_PER_DAY = 86400000

    difference_in_milli = timestamp_2 - timestamp_1

    difference = int(difference_in_milli / MILLI_PER_DAY)

    return difference


'''
determines if two time stamps are in the same time period 
@params 
    - timestamp_1: first time stamp 
    - timestamp_2: second time stamp
    - Timestamps: dictionary of timestamps for the four time periods used and the current timestamp
                  timestamps are unix timestamps, in milliseconds represented as integers 
@returns
    - time_period: time period that both timestamps are in or null if timestamps are not within the same time period 
'''
def get_similar_timeperiod(timestamp_1, timestamp_2, Timestamps):

    if (Timestamps[0] > timestamp_1) and (Timestamps[0] > timestamp_2) and (timestamp_1 > Timestamps[1]) and (timestamp_2 > Timestamps[1]): #in the past month
        time_period = '1_month'

    elif (Timestamps[1] > timestamp_1) and (Timestamps[0] > timestamp_2) and (timestamp_1 > Timestamps[3])and (timestamp_2 > Timestamps[3]): #between the past month and past 3 months   
        time_period = '3_months'

    elif (Timestamps[3] > timestamp_1) and (Timestamps[0] > timestamp_2) and (timestamp_1 > Timestamps[6]) and (timestamp_2 > Timestamps[6]): #between the past 3 months and past 6 months
        time_period = '6_months'

    elif (Timestamps[6] > timestamp_1) and (Timestamps[0] > timestamp_2) and (timestamp_1 > Timestamps[12]) and (timestamp_2 > Timestamps[12]) : #between the past 6 months and past year
        time_period = '12_months'
    else:
        time_period = 0

    return time_period


'''
determines the timeperiod a timestamp falls in
@params 
    - timestamp_1: first time stamp 
    - timestamp_2: second time stamp
    - Timestamps: dictionary of timestamps for the four time periods used and the current timestamp
                  timestamps are unix timestamps, in milliseconds represented as integers 
@returns
    - time_period: time period that both timestamps are in or null if timestamps are not within the same time period 
'''
def get_current_timeperiod(timestamp, Timestamps):
    time_period = None

    if (Timestamps[0] > timestamp) and (timestamp > Timestamps[1]): #in the past month
        time_period = '1_month'

    elif (Timestamps[1] > timestamp) and  (timestamp > Timestamps[3]): #between the past month and past 3 months   
        time_period = '3_months'

    elif (Timestamps[3] > timestamp)  and (timestamp > Timestamps[6]): #between the past 3 months and past 6 months
        time_period = '6_months'

    elif (Timestamps[6] > timestamp)  and (timestamp > Timestamps[12]): #between the past 6 months and past year
        time_period = '12_months'
    else: 
        time_period = None

    return time_period


'''
function to get the time since last batch for each part
@params
    - current_timestamp: timestamp from when get_timestamps function was called
                         unix timestamp, in milliseconds represented as an integer
    - sorted_stock: sorted stock data 
@returns
    - sorted_stock: sorted stock data with added data to each part for time since last batch 
'''
def get_time_since_last_batch(current_timestamp, sorted_stock):
    for part in sorted_stock: 
        stock_history = sorted_stock[part]['stock']
        length = len(stock_history)
        stock_index = length - 1

        last_batch = stock_history[stock_index]['stock/timestamp']
        time_since_last_batch = get_difference(last_batch, current_timestamp)
        sorted_stock[part]["days_since_last_batch"] = time_since_last_batch
        date = datetime.fromtimestamp(last_batch/1000) #convert timestamp to seconds from milliseconds 
        date = datetime.date(date)
        format_string = '%Y-%m-%d'
        # Convert the datetime object to a string in the specified format
        date_string = date.strftime(format_string)
        sorted_stock[part]['date_last_batch'] = date_string       

    return sorted_stock


'''
function to get date of last acquisition of parts 
@params
    - current_timestamp: timestamp from when get_timestamp function was called, 
                         unix timestamp, in milliseconds represented as an integer 
    - parts: list of dictionaries with full response from api request 
@returns 
    - parts: parts data with added feild for date of last acquisition 
'''
def get_date_of_last_restock(current_timestamp, parts):
    part_entry = 0

    for part in parts: 
        stock = parts[part_entry]["part/stock"]
        length = len(stock) 

        if length <= 0: #if no stock history
            parts[part_entry]["date_last_restock"] = None
        else:
            stock_entry = get_restock_entry(parts, length, part_entry)
        if stock_entry == None:
            parts[part_entry]["date_last_restock"] = None
        else:
            last_restock = parts[part_entry]['part/stock'][stock_entry]['stock/timestamp']
            date = datetime.fromtimestamp(last_restock/1000) #convert timestamp to seconds from milliseconds first
            date = datetime.date(date)
            format_string = '%Y-%m-%d'
            # Convert the datetime object to a string in the specified format
            date_string = date.strftime(format_string)
            parts[part_entry]["date_last_restock"] = date_string         

        part_entry += 1

    return parts

'''
function that determines the most recent restock based on comments not containing 'move'
and quantity being positive 
@params 
    - parts:
    - stock_index: 
@returns 
    - 

'''
def get_restock_entry(parts, stock_index, part_entry):
    #initalize flags
    comment = False
    positive = False

    #loop until most recent entry that is a restock 
    while (comment == False) or (positive == False):
        #loop until most recent entry that is a restock 
        if stock_index > 0: 
            stock_index -= 1
            quantity = parts[part_entry]['part/stock'][stock_index]['stock/quantity']

            try:
                comment = parts[part_entry]['part/stock'][stock_index]['stock/comments']
                word = 'moved'
                #check if stock entry was for moving stock
                if word in comment.lower():
                    comment = False
                else: 
                    comment = True
            except KeyError: #no comment
                comment = True
                    
            #check if stock entry was a batch or a restock
            if quantity >= 0:
                positive = True
            else: 
                positive = False

        else: 
            comment = True 
            positive = True
            stock_index = None

    return stock_index



""" Testing the functions """
if __name__ == '__main__':
    print(get_timestamps())