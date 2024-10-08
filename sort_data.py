"""
Module that contains functions for sorting data for partsbox api interface, and for pushing data to airtable 
"""

import json 
import pandas as pd
import csv
from ratelimit import limits
from alive_progress import alive_bar
from alive_progress.styles import showtime
import time
import requests

#defining constants for indexing api keys 
WRITE = 0
READ = 1 


"""
function that checks if parts have a valid lead time field and if not adds a custom field with the default lead time
@params	
	- parts: list of part data from partsbox api response 
@returns
	- parts: with added lead times field for parts that had invalid or non existent lead times 

"""
#TODO add robustness for if there is other custom fields 
def update_lead_times(parts):
	valid = True
	part_id = parts[0]['part/id']
	#printing for testing
	print(part_id)
	#printing for testing 
	part_lead = get_lead(parts, 0)
	print(part_lead)

	#check for lead times that are negative or 0 
	if int(part_lead) <= 0: 
		#set to default of 2 weeks 
		valid = False
	#printing for testing 
	print(valid)

	if valid == False: 
		try: 
			with open("partsbox_config.json") as config_file: 
				config = json.load(config_file)
		except FileNotFoundError: 
			print("no config file found")
			f = open("partsbox_config.json", "x")
			f.close
			print("partsbox_config.json file created, populate file with your api key and rerun program!\n the format for the config file is as follows\n {'API_key': 'APIKey enter_your_api_key_here'}")

		headers = {
		'Authorization': config[WRITE]["API_key"] 
		}

		url = 'https://api.partsbox.com/api/1/part/update-custom-fields' 

		payload = {"part/id": part_id,  "custom-fields": [{"key": "lead_time_(weeks)", "value": "2"}]}
		print(payload)

		json_data = requests.post(url, headers=headers, json = payload).json()

		print()
		print()
		print(json_data)
		print()
		print()


'''
function that searches for a custom field for lead times 
@params
	- parts: list of data for all parts 
	- parts_index: index for parts list 
@returns
	- leadtime: leadtime if found or 0 otherwise
'''
def get_lead(parts, parts_index):
	try: #check if part has valid lead time
		custom_fields = parts[parts_index]["part/custom-fields"]
		field_index = 0

		for field in custom_fields: 
			if custom_fields[field_index]["key"] == "lead_time_(weeks)":
				leadtime = custom_fields[field_index]["value"]
			else:
				leadtime = 0 

			field_index += 1

	except KeyError: #no data
		#set to default lead time of 2 weeks 
		leadtime = 0

	return leadtime







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

			#check if stock update is for production or procurement
			if part_quantity >= 0:
				negative = False
			else:
				negative = True

			#if for production add to stock list 
			if (valid==True)and(negative==True):
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
	- refined_data: list of parts that have had valid stock history within the past year 
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
	- refined_data: list of parts that have had valid stock history within the past year 
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
function that sorts data to be pushed to air table
@params
	- sorted_stock: nested dictionary containg data for all valid parts
@returns 
	- airtable_data: airtable data for all parts, formatted as a list so it can be easily broken in to groups of 10 for pushing to airtable

'''
def get_data_for_airtable(sorted_stock):
	airtable_data = []

	part_index = 0

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
				'risk': risk,
				'rop_estimate': rop_estimate, 
				'last_batch': last_batch,
				'last_restock': last_restock}

		data = {"fields": entry}

		airtable_data.append(data)


	return airtable_data


'''
function that prepares part data for pushing to airtable in groups of no more than 10
@params
	- airtable_data: list of parts left to be pushed to airtable
@returns:
	- group_of_ten: a list containing data for up to 10 parts

'''
def get_group_of_ten(airtable_data):
	test_index = 0
	group_of_ten = []

	length = len(airtable_data)
	while test_index < 10 and test_index <= length-1:
		group_of_ten.append(airtable_data.pop(0))
		test_index += 1

	return group_of_ten


TIME_PERIOD = 1 #time period in seconds (airtable is limited to 5 requests per second)	
'''
limits decorator ensures only 5 calls per second can be made, to meet the rate limit of airtables api 
@params
	- calls: number of calls (integer) that can take place during one period 
	- period: amount of seconds for rate limiting 
@returns 
	- none

function that pushes data to airtable for all valid parts 
@params
	- airtable_data: list of all data to be pushed to airtable 
@returns: 
	- none
'''
@limits(calls = 5, period = TIME_PERIOD)
def push_to_airtable(airtable_data):
	length = len(airtable_data)
	number_of_calls = int(length / 10) + (length % 10 > 0) 
	with alive_bar(number_of_calls, bar = 'fish') as bar: #set up progress bar based off of number of calls to be made
		for i in range(number_of_calls):
			#get arrray of ten parts
			data_to_push = get_group_of_ten(airtable_data)
			length = len(airtable_data)

			#get authorization token
			try: 
				with open("airtable_config.json") as c_file: 
					config = json.load(c_file)
			except FileNotFoundError: 
				print("no config file found")
				f = open("airtable_config.json", "x")
				f.close
				print("config.json file created, populate file with your api key and rerun program!\n the format for the config file is as follows\n {'API_key': 'APIKey enter_your_api_key_here'}")

			headers = {
			'Authorization': config["Authorization"],
			"Content-Type" : "application/json"
			}

			data = {}
			list_of_fields = []
			list_of_fields.append("part_id")
			list_of_fields.append('description')

			entry = {"fieldsToMergeOn": list_of_fields}
			data = {"performUpsert": entry, "records": data_to_push}

			url = "https://api.airtable.com/v0/appRz7kFjf3jJ9Xe4/tblHGveIi8Oy1XoeA" 

			#commented out to stop calling the api while adding extra features
			json_result = requests.patch(url, headers=headers, json = data)
			#print statement for testing
			print(json_result)

			bar() #update progress bar 





	 