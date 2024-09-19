"""
Module containing functions to complete necessary calculations for partsbox api interface 
"""

import time_stamp


"""
calculate total stock count for each item 
@params 
	-parts: data from api response/cache 
@returns 
	-parts: data from api/response with appended data for stock counts 
"""
def total_stock(parts):
	part_entry = 0

	for part in parts:
		stock_count = 0

		try:
			part_stock = parts[part_entry]['part/stock']
			stock_entry = 0

			for stock in part_stock:
				stock_count  = stock_count + parts[part_entry]['part/stock'][stock_entry]['stock/quantity']
				stock_entry = stock_entry + 1

		except KeyError:
			stock_count = None

		#add key value pair with total stock count to each part 
		parts[part_entry]['part/total_stock'] = stock_count
		part_entry = part_entry + 1

	return parts



"""
Function to calculate the average batch size for 4 time periods 
@params 
	- Timestamps: dictionary of timestamps 
	- sorted_stock: sorted data from api response/cache 
@returns 
	- sorted_stock: data from api request with dictionary of average batch sizes added 
"""
def get_avg_batch(sorted_stock, Timestamps):
	part_entry = 0

	for part in sorted_stock:
		batch_tot_1 = 0
		batch_tot_3 = 0
		batch_tot_6 = 0
		batch_tot_12 = 0
		data_points_1 = 0
		data_points_3 = 0
		data_points_6 = 0
		data_points_12 = 0

		#if part has stock
		try:
			part_stock = sorted_stock[part_entry]['stock']
			batch_total = 0
			stock_entry = 0

			for stock in part_stock:
				timestamp = part_stock[stock_entry]['stock/timestamp']

				if Timestamps[0] > timestamp and timestamp > Timestamps[1]: #in the past month
					batch_tot_1 = batch_tot_1 + sorted_stock[part_entry]['stock'][stock_entry]['stock/quantity']
					data_points_1 = data_points_1 + 1

				elif Timestamps[1] > timestamp and timestamp > Timestamps[3]: #between the past month and past 3 months 
					batch_tot_3 = batch_tot_3 + sorted_stock[part_entry]['stock'][stock_entry]['stock/quantity']
					data_points_3 = data_points_3 + 1

				elif Timestamps[3] > timestamp and timestamp > Timestamps[6]: #between the past 3 months and past 6 months 
					batch_tot_6 = batch_tot_6 + sorted_stock[part_entry]['stock'][stock_entry]['stock/quantity']
					data_points_6 = data_points_6 + 1

				elif Timestamps[6] > timestamp and timestamp > Timestamps[12]: # between the past 6 months and past year 
					batch_tot_12 = batch_tot_12 + sorted_stock[part_entry]['stock'][stock_entry]['stock/quantity']
					data_points_12 = data_points_12 + 1

				else:
					pass

				stock_entry += 1

		except KeyError: 

			avg_batch = None

		#calculate cumulative values for batch totals and data points 
		batch_tot_3 = batch_tot_3 + batch_tot_1
		data_points_3 = data_points_3 + data_points_1

		batch_tot_6 = batch_tot_6 + batch_tot_3
		data_points_6 = data_points_6 + data_points_3

		batch_tot_12 = batch_tot_12 + batch_tot_6
		data_points_12 = data_points_12 + data_points_6

		#calculate averages
		try:
			batch_avg_1 = batch_tot_1 / data_points_1
		except ZeroDivisionError:
			batch_avg_1 = None 

		try:
			batch_avg_3 = batch_tot_3 / data_points_3
		except ZeroDivisionError:
			batch_avg_3 = None 

		try:
			batch_avg_6 = batch_tot_6 / data_points_6
		except ZeroDivisionError:
			batch_avg_6 = None 
			
		try:
			batch_avg_12 = batch_tot_12 / data_points_12
		except ZeroDivisionError:
			batch_avg_12 = None 

		averages = [batch_avg_1, batch_avg_3, batch_avg_6, batch_avg_12]
		average_for_calculations = get_weighted_average(averages)

		#add averages to dictionary 
		sorted_stock[part_entry]['batch/average_1_months'] = batch_avg_1
		sorted_stock[part_entry]['batch/average_3_months'] = batch_avg_3
		sorted_stock[part_entry]['batch/average_6_months'] = batch_avg_6
		sorted_stock[part_entry]['batch/average_12_months'] = batch_avg_12
		sorted_stock[part_entry]['batch/average_for_calculations'] = average_for_calculations

		#increase part counter 
		part_entry = part_entry + 1

	return sorted_stock


"""
Function to calculate the average time between batches for 4 time periods 
@params
	- Timestamps: dictionary of timestamps 
	- sorted_stock: dictionary of sorted data from api response/cache 
@returns 
	- sorted_stock: sorted stock data with dictionary of average times between batches added
"""
def get_avg_time(sorted_stock, Timestamps): 
	part_entry = 0

	for part in sorted_stock: 
		time_tot_1 = 0
		time_tot_3 = 0
		time_tot_6 = 0
		time_tot_12 = 0
		time_avg_1 = None
		time_avg_3 = None
		time_avg_6 = None
		time_avg_12 = None
		data_points_1 = 0
		data_points_3 = 0
		data_points_6 = 0
		data_points_12 = 0
		part_stock = sorted_stock[part_entry]['stock']
		stock_entry = 0
		stock_history_size = len(part_stock)

		for stock in part_stock:
			timestamp = part_stock[stock_entry]['stock/timestamp']
			time_period = None
			next_stock_entry = stock_entry + 1

			if next_stock_entry <= (stock_history_size - 1):
				next_timestamp = part_stock[next_stock_entry]['stock/timestamp']
				difference = time_stamp.get_difference(timestamp, next_timestamp)
				time_period = time_stamp.get_timeperiod(timestamp, next_timestamp, Timestamps)

			else: 
				difference = 0

			if time_period == 1: #in the past month
	 			time_tot_1 = time_tot_1 + difference
	 			data_points_1 = data_points_1 + 1

			elif time_period == 3: #between the past month and past 3 months
	 			time_tot_3 = time_tot_3 + difference
	 			data_points_3 = data_points_3 + 1

			elif time_period == 6: #between the past 3 months and past 6 months
	 			time_tot_6 = time_tot_6 + difference
	 			data_points_6 = data_points_6 + 1

			elif time_period == 12: #between the past 6 months and past year
	 			time_tot_12 = time_tot_12 + difference
	 			data_points_12 = data_points_12 + 1

			else:
	 			pass

			stock_entry += 1

	 	#calculate cumulative values for batch totals and data points 
		time_tot_3 = time_tot_3 + time_tot_1
		data_points_3 = data_points_3 + data_points_1

		time_tot_6 = time_tot_6 + time_tot_3
		data_points_6 = data_points_6 + data_points_3

		time_tot_12 = time_tot_12 + time_tot_6
		data_points_12 = data_points_12 + data_points_6 

	 	#calculate averages
		try:
	 		time_avg_1 = time_tot_1 / data_points_1
		except ZeroDivisionError:
	 		time_avg_1 = None 
	 	
		try:
	 		time_avg_3 = time_tot_3 / data_points_3
		except ZeroDivisionError:
	 		batch_avg_3 = None 

		try:
	 		time_avg_6 = time_tot_6 / data_points_6
		except ZeroDivisionError:
	 		batch_avg_6 = None 

		try:
	 		time_avg_12 = time_tot_12 / data_points_12
		except ZeroDivisionError:
	 		batch_avg_12 = None 

		averages = [time_avg_1, time_avg_3, time_avg_6, time_avg_12]
		average_for_calculations = get_weighted_average(averages)

	 	#add averages to dictionary 
		sorted_stock[part_entry]['time/average_1_months'] = time_avg_1
		sorted_stock[part_entry]['time/average_3_months'] = time_avg_3
		sorted_stock[part_entry]['time/average_6_months'] = time_avg_6
		sorted_stock[part_entry]['time/average_12_months'] = time_avg_12
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
	year_average = averages[3] 

	if year_average != None: #if there is data for the past year
		tolerance = year_average * 0.15
		lower_bound = int(averages[3] - tolerance)
		upper_bound = int(averages[3] + tolerance)
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
		if averages[i] == 0 or averages[i] == None:
			zero_count = zero_count + 1
			i += 1 

	i = 0 
	#determine if a weighted average needs to be calculated or if the 12 month average should be used
	while (weighted_flag == False) and (i <= 3):
		average = averages[i]

		if average != None: 
			if lower_bound <= average <= upper_bound:
				weighted_flag = False
			else: 
				weighted_flag = True
		else: 
			averages[i] = 0

		i += 1 

	divisor = [10, 6, 3, 1]
	if weighted_flag == True:
		average_for_calculations = (averages[0] * 4) + (averages [1]* 3) + (averages[2] * 2) + (averages[3] * 1)
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
def get_risk_level(sorted_stock, current_timestamp): 
	part_entry = 0 

	for part in sorted_stock: 
		estimated_rop = 0
		approx_lead_time = 7
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
			estimated_rop = number_of_batches * avg_time

		#print for testing 
		print('estimated ROP', int(estimated_rop))

		if avg_time == None or avg_time == 0: #either no stock entries or only one therefore unlikely for more batches to be produced
			sorted_stock[part_entry]['risk_level'] = 'Low - not enough data'
		else: 
			if (estimated_rop < 0):
				sorted_stock[part_entry]['risk_level'] = 'High - overdue for batch'
			elif (0 <= estimated_rop <= 14): 
				sorted_stock[part_entry]['risk_level'] = 'High'
			elif (14 < estimated_rop <= 28):
				sorted_stock[part_entry]['risk_level'] = 'Medium'
			elif (estimated_rop > 28):
				sorted_stock[part_entry]['risk_level'] = 'Low'

		#print for testing 
		print('risk level', sorted_stock[part_entry]['risk_level'])
		print()
		print()

		part_entry += 1

	return sorted_stock

