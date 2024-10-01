"""
Module that contains functions for sorting data for partsbox api interface 
"""

import json 
import pandas as pd
import csv


"""
Function to sort the data from api response to have just the batch data
@params 
	- parts: data from api response/cache 
	- Timestamps: dictionary of timestamps for the four time periods used, and the current timestamp
				  timestamps are unix timestamps, in milliseconds represented as integers 
@returns 
	- stock_list: dictionary of sorted data 
"""
def sort(parts, Timestamps):
	part_entry = 0
	#create an empty dictionary to store all stock data 
	stock_list = {}

	""" 
	iterate through parts in data 
	for each part get stock information and id 
	create dictionary entries that holds all the IDs, Descriptions, and stock info 
	append dictionary to list 
	"""
	for part in parts:
		add_part_flag = False; 

		#get wanted variables 
		part_id = parts[part_entry]['part/id']
	
		try:
			part_description = parts[part_entry]['part/description']
		except KeyError as e: #entry does not contain a description
			#added notes for exception, will only show if code is changed so exception is raised
			e.add_note(f"{part_id} does not contain the data field 'part/description'")
			part_description = None
		try:
			part_mpn = parts[part_entry]['part/mpn']
		except KeyError as e: #entry does not contain an mpn
			part_mpn = None
			e.add_note(f"{part_id} does not contain the data field 'part/mpn'")
		try: 
			part_stock_count = parts[part_entry]['part/total_stock']
		except KeyError as e: #entry does not contain a total stock count
			part_stock_count = None
			e.add_note(f"{part_id} does not contain the data field 'part/total_stock'")
		try:
			part_stock = parts[part_entry]['part/stock']
		except KeyError as e:#entry does not contain a stock history
			part_stock = None
			e.add_note(f"{part_id} does not contain the data field 'part/stock'")
		try:
			part_restock = parts[part_entry]["date_last_restock"]
		except KeyError as e: 
			part_restock = None
			e.add_note(f"{part_id} does not contain the data field 'date_last_restock'")


		#create dictionary of data feilds for parts
		stock_list[part_id] = {'description': part_description, 'mpn': part_mpn, 'total_stock': part_stock_count, 'part/restock': part_restock}

		#create empty list for valid stock entries for each part
		valid_stock = []
		#set stock entry counter to 0 for each part 
		stock_entry=0

		"""
			Loop through stock entries
			Discard entries that have strings with 'move' in them
			Discard postive entries 
			Discard entries that do not have stock entries from the past year 
		"""
		#if part_stock != None:

		for stock in part_stock:

			#set valid and negative flags 
			valid = True
			negative = False
			last_year = False				
			#get stock data
			stock_data = parts[part_entry]['part/stock'][stock_entry]
			part_quantity = parts[part_entry]['part/stock'][stock_entry]['stock/quantity']

			# check if stock update is for moving parts not production
			try:
				comment = parts[part_entry]['part/stock'][stock_entry]['stock/comments']
				word = 'moved'
				if word in comment.lower():
					valid = False
			except KeyError:#entry in stock history does not contain a comment 
				pass
			try: 
				stock_timestamp = parts[part_entry]['part/stock'][stock_entry]['stock/timestamp']
			except KeyError: #entry in stock history does not contain a timestamp
				stock_timestamp = None

			#check if stock update is for production or procurement
			if part_quantity >= 0:
				negative = False
			else:
				negative = True

			#check if stock entry is from the past year 
			if stock_timestamp != None: 
				if stock_timestamp >= Timestamps[12]: 
					last_year = True

			#if for production add to stock list 
			if (valid==True)and(negative==True)and(last_year==True):
				valid_stock.append(stock_data)
				add_part_flag == True

			#increase stock counter 
			stock_entry = stock_entry + 1

		#add valid stock to stock list entries
		stock_list[part_id]['stock'] = valid_stock

		part_entry += 1


	return stock_list



'''
function to remove entries in the sorted data that have no valid stock history 
@params 
	- parts: list of all parts data
@returns 
	- refined_stock: list of parts that have had valid stock history within the past year 
'''
def remove_empty_stock_list(parts):
	part_entry = 0 
	refined_data = []

	for part in parts: 
		data = parts[part_entry]
		valid = True

		try:
			stock_data = parts[part_entry]['part/stock']
		except KeyError: #entry does not exist 
			valid = False

		if stock_data == []:
			valid = False

		if valid == True: 
			refined_data.append(data) #add part entry to list if stock history is valid

		part_entry += 1 

	return refined_data


'''
function to remove entries in the sorted data that have no valid stock history 
@params 
	- sorted_stock: nested dictionary of valid part information 
@returns 
	- refined_stock: list of parts that have had valid stock history within the past year 
'''
def remove_empty_stock_dict(sorted_stock):
	refined_data = {}

	for part in sorted_stock: 
		data = sorted_stock[part]
		valid = True

		try:
			stock_data = sorted_stock[part]['stock']
		except KeyError: #entry does not exist 
			valid = False

		if stock_data == []:
			valid = False

		if valid == True: 
			refined_data[part] = data

	return refined_data


'''
function that takes json data, takes data that is to be pushed to airtable and creates a json file and a csv file
@params
	- sorted_stock: list containgin json data for all valid parts int he past year 
@returns 
	- none

'''
#TODO: get rid of the json file and read into csv from json string?
def get_data_for_airtable(sorted_stock):
	json_data_for_airtable = []

	for part in sorted_stock: 
		part_id = part
		description = sorted_stock[part]['description']
		mpn = sorted_stock[part]['mpn']
		total_stock = sorted_stock[part]['total_stock']
		last_batch = sorted_stock[part]['date_last_batch']
		last_restock = sorted_stock[part]['part/restock']
		risk = sorted_stock[part]['risk_level']
		rop_estimate = int(sorted_stock[part]['estimated_rop'])

		entry = {'part_id': part_id,
				'description': description, 
				'mpn': mpn, 
				'total_stock': total_stock, 
				'last_batch': last_batch, 
				'last_restock': last_restock,
				'risk': risk, 
				'rop_estimate': rop_estimate}

		#add part data to stock list 
		json_data_for_airtable.append(entry)

	# Serializing json
	json_object = json.dumps(json_data_for_airtable, indent=4, default = str)
	 
	# Writing to sample.json

	with open("sample.json", "w") as outfile:
		outfile.write(json_object)

	data = pd.read_json("sample.json")
	data.to_csv('sample.csv')








		

	






