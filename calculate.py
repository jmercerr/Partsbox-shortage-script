"""
Module containing functions to complete necessary calculations for partsbox api interface 
"""

import time_stamp


"""
calculate total stock count for each item 
@params 
	-parts: json data from api response/cache
@returns 
	-parts: data from api/response with appended data for stock counts 
"""
def total_stock(parts):
	part_entry = 0

	for part in parts:
		stock_count = 0
		part_stock = parts[part_entry]['part/stock']
		stock_entry = 0

		for stock in part_stock:
			stock_count  = stock_count + parts[part_entry]['part/stock'][stock_entry]['stock/quantity']
			stock_entry = stock_entry + 1

		#add key value pair with total stock count to each part 
		parts[part_entry]['part/total_stock'] = stock_count
		part_entry = part_entry + 1

	return parts



"""
Function to calculate the average batch size for 4 time periods 
@params 
    - Timestamps: dictionary of timestamps for the four time periods used and the current timestamp
                  timestamps are unix timestamps, in milliseconds represented as integers 
  	- sorted_stock: sorted data from api response/cache 
@returns 
	- sorted_stock: data from api request with dictionary of average batch sizes added 
"""
def get_avg_batch(sorted_stock, Timestamps):
	part_entry = 0

	for part in sorted_stock:
		batch_totals = {'1_month': 0, '3_months': 0, '6_months': 0, '12_months': 0}
		batch_averages = {'1_month': 0, '3_months': 0, '6_months': 0, '12_months': 0}
		data_points = {'1_month': 0, '3_months': 0, '6_months': 0, '12_months': 0}
		time_periods = ['1_month', '3_months', '6_months', '12_months']

		#if part has stock
		batch_total = 0
		stock_entry = 0

		part_stock = sorted_stock[part_entry]['stock']

		for stock in part_stock:
			timestamp = part_stock[stock_entry]['stock/timestamp']

			#call get time period function 
			time_period = time_stamp.get__current_timeperiod(timestamp, Timestamps)

			#increase batch total based on time period 
			batch_totals[time_period] = batch_totals[time_period] + sorted_stock[part_entry]['stock'][stock_entry]['stock/quantity']

			#increase data points based on time period
			data_points[time_period] = data_points[time_period] + 1

			stock_entry += 1

		#calculate cumulative values for batch totals and data points 
		i = 1
		while i <= 3:
			batch_totals[time_periods[i]] = batch_totals[time_periods[i]] + batch_totals[time_periods[i-1]]
			data_points[time_periods[i]] = data_points[time_periods[i]] + data_points[time_periods[i - 1]]
			i += 1 


		#calculate averages
		i=0
		while i <= 3:
			try:
				batch_averages[time_periods[i]] = batch_totals[time_periods[i]] / data_points[time_periods[i]]
			except ZeroDivisionError:
				batch_averages[time_periods[i]] = 0
			i += 1


		average_for_calculations = get_weighted_average(batch_averages)

		#add averages to dictionary 
		sorted_stock[part_entry]['batch/averages'] = batch_averages
	
		sorted_stock[part_entry]['batch/average_for_calculations'] = average_for_calculations

		#increase part counter 
		part_entry = part_entry + 1

	return sorted_stock


"""
Function to calculate the average time between batches for 4 time periods 
@params
	- Timestamps: dictionary of timestamps for the four time periods used and the current timestamp
                  timestamps are unix timestamps, in milliseconds represented as integers 
	- sorted_stock: dictionary of sorted data from api response/cache 
@returns 
	- sorted_stock: sorted stock data with dictionary of average times between batches added
"""
def get_avg_time(sorted_stock, Timestamps): 
	part_entry = 0

	for part in sorted_stock: 
		time_totals = {'1_month': 0, '3_months': 0, '6_months': 0, '12_months': 0}
		time_averages = {'1_month': 0, '3_months': 0, '6_months': 0, '12_months': 0}
		data_points = {'1_month': 0, '3_months': 0, '6_months': 0, '12_months': 0}
		time_periods = ['1_month', '3_months', '6_months', '12_months']

		part_stock = sorted_stock[part_entry]['stock']
		stock_entry = 0
		stock_history_size = len(part_stock)

		for stock in part_stock:
			timestamp = part_stock[stock_entry]['stock/timestamp']
			time_period = 0
			next_stock_entry = stock_entry + 1

			if next_stock_entry <= (stock_history_size - 1):
				next_timestamp = part_stock[next_stock_entry]['stock/timestamp']
				difference = time_stamp.get_difference(timestamp, next_timestamp)
				time_period = time_stamp.get_similar_timeperiod(timestamp, next_timestamp, Timestamps)

			else: 
				difference = 0

			if time_period != 0:
				time_totals[time_period] = time_totals[time_period] + difference
				data_points[time_period]= data_points[time_period] + 1

			else:
	 			pass

			stock_entry += 1

		#calculate cumulative values for batch totals and data points 
		i = 1
		while i <= 3:
			time_totals[time_periods[i]] = time_totals[time_periods[i]] + time_totals[time_periods[i-1]]
			data_points[time_periods[i]] = data_points[time_periods[i]] + data_points[time_periods[i - 1]]
			i += 1 


		#calculate averages
		i=0
		while i <= 3:
			try:
				time_averages[time_periods[i]] = time_totals[time_periods[i]] / data_points[time_periods[i]]
			except ZeroDivisionError:
				time_averages[time_periods[i]] = 0
			i += 1

		average_for_calculations = get_weighted_average(time_averages)

	 	#add averages to dictionary 
		sorted_stock[part_entry]['time/averages'] = time_averages
		sorted_stock[part_entry]['time/average_for_calculations'] = average_for_calculations

	 	#increase part counter 
		part_entry = part_entry + 1

	return sorted_stock


''' 
determines whether 4 averages for a part are relatively similar or if a weighted average must be calculated 
@params
	- averages: a dictionary containing 4 averages for the 4 time periods
@returns
	- true_average: weighted average if averages are not relatively similar, year average otherwise
'''
def get_weighted_average(averages):
	time_periods = ['1_month', '3_months', '6_months', '12_months']
	year_average = averages["12_months"] 

	if year_average != 0: #if there is data for the past year
		tolerance = year_average * 0.15
		lower_bound = int(averages['12_months'] - tolerance)
		upper_bound = int(averages['12_months'] + tolerance)

	else: 
		year_average = 0
		tolerance = 0
		lower_bound = 0
		upper_bound = 0

	#initalize variables for indexing, counts, and flags
	weighted_flag = False
	average_for_calculations = 0
	i = 0
	zero_count = 0

	for average in averages:
		#count number of null or zero values, to be used as index into dizisor list
		if averages[time_periods[i]] == 0:
			zero_count = zero_count + 1
			i += 1 

	i = 0 
	#determine if a weighted average needs to be calculated or if the 12 month average should be used
	while (weighted_flag == False) and (i <= 3):
		average = averages[time_periods[i]]

		if average != 0: 
			if lower_bound <= average <= upper_bound:
				weighted_flag = False
			else: 
				weighted_flag = True

		i += 1 

	divisor = [10, 6, 3, 1]
	if weighted_flag == True:
		average_for_calculations = (averages['1_month'] * 4) + (averages ['3_months']* 3) + (averages['6_months'] * 2) + (averages['12_months'] * 1)
		average_for_calculations = average_for_calculations / divisor[zero_count]

	else: 
		average_for_calculations = year_average

	return average_for_calculations



''' 
function to calculate the risk level of running out of each part 
	- high = likely to run out in next 2 weeks 
	- medium = likely to run out in next 3-4 weeks 
	- low = likely to run out in over a month 
			no stock data or only 1 data point - unlikely for future batches to take place 
@params 
	- sorted_stock: list with all sorted_data and added feilds from previous calculations 
	- current_timestamp: timestamp from when the program was run 
@returns
	- sorted_stock: with added risk level and estimated time till no stock 
'''
#TODO: approx_lead_time variable with default lead time will be set for every part figure out a way to pass in a lead time for each 
def get_risk_level(sorted_stock, current_timestamp, approx_lead_time = 7): 
	part_entry = 0 

	for part in sorted_stock: 
		estimated_rop = 0
		sorted_stock[part_entry]['risk_level'] = None
		current_stock = sorted_stock[part_entry]['total_stock']
		current_stock = abs(current_stock)
		avg_batch = sorted_stock[part_entry]['batch/average_for_calculations']
		avg_batch = abs(avg_batch)
		avg_time = sorted_stock[part_entry]['time/average_for_calculations']
		last_batch = sorted_stock[part_entry]['time/last_batch']

		if last_batch >= avg_time: #overdue for a batch to be produced
			time_till_next_batch = -abs(int(last_batch - avg_time))
		else: 
			time_till_next_batch = abs(int(last_batch - avg_time))

		#print for testing 
		print('time since last batch', last_batch)
		print('time till next batch', time_till_next_batch)
		print('average time:', avg_time)

		number_of_batches = int(current_stock / avg_batch) 

		#print for testing 
		print('number of batches that can be produced', number_of_batches)

		if number_of_batches == 0: #next batch will require more stock before it can be completed 
			estimated_rop =  time_till_next_batch - approx_lead_time
		else:
			estimated_rop = (number_of_batches * avg_time) - approx_lead_time

		#print for testing 
		print('estimated ROP', int(estimated_rop))
		sorted_stock[part_entry]['estimated_rop'] = estimated_rop

		if avg_time == None or avg_time == 0: #either no stock entries or only one therefore unlikely for more batches to be produced
			sorted_stock[part_entry]['risk_level'] = 'Low - not enough data'
		else: 
			if (estimated_rop < 0):
				sorted_stock[part_entry]['risk_level'] = 'High - overdue for batch'
			elif (0 <= estimated_rop <= 30): 
				sorted_stock[part_entry]['risk_level'] = 'High'
			elif (30 < estimated_rop <= 90):
				sorted_stock[part_entry]['risk_level'] = 'Medium'
			elif (estimated_rop > 90):
				sorted_stock[part_entry]['risk_level'] = 'Low'

		#print for testing 
		print('risk level', sorted_stock[part_entry]['risk_level'])
		print()
		print()

		part_entry += 1

	return sorted_stock

