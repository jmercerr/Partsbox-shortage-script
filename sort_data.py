"""
Module that contains functions for sorting data for partsbox api interface, and for pushing data to airtable 

"""

import json 
import pandas as pd
import time
import requests
import csv
from ratelimit import limits, sleep_and_retry
from alive_progress import alive_bar
from alive_progress.styles import showtime
import cache

#defining constants for indexing api keys 
WRITE = 0
READ = 1 
REQUESTS = 200 
TIME_PERIOD = 60 #(seconds)

@sleep_and_retry
@limits(calls = REQUESTS, period = TIME_PERIOD)
def check_partsbox_limit():
	"""
	Empty function for checking calls to the PartsBox API.

	Should be called at the beggining of every function that makes a request to PartsBox 
	currently partsbox does not enforce rate limiting but if they do change calls and rate_limit to match their listed limits

	"""
	return


def update_lead_times(parts, headers):	
	"""
	Check if parts have a valid lead time and adds default lead time if not. 

	@params	
		- parts: list of part data from partsbox api response 
		- headers: headers data including authorization key for api call 
	@returns
		- parts: with added lead times field for parts that had invalid or non existent lead times 
	"""
	valid = True
	part_entry = 0

	for part in parts: 
		part = parts[part_entry]
		part_id = parts[part_entry]["part/id"]
		part_lead = get_lead(part)
		
		#check for lead times that are negative or 0 
		if int(part_lead) <= 0: 
			#set to default of 2 weeks 
			valid = False

		if not valid: 
			url = "https://api.partsbox.com/api/1/part/update-custom-fields"
			payload = {"part/id": part_id,  "custom-fields": [{"key": "lead_time_(weeks)", "value": "2"}]}
			json_data = requests.post(url, headers = headers, json = payload).json()
			part_lead = 2 #set to default

		part_entry += 1

	return parts


def get_lead(part):
	"""
	Search for a custom field for lead times.

	@params
		- part: data for a single part from the parts list  
	@returns
		- leadtime: leadtime if found or 0 otherwise
	"""	
	try: #check if part has valid lead time
		custom_fields = part["part/custom-fields"]
		field_index = 0
		leadtime = 0

		#loop through custom fields to find lead time if field exists
		for field in custom_fields: 
			if custom_fields[field_index]["key"] == "lead_time_(weeks)":
				leadtime = custom_fields[field_index]["value"]

			field_index += 1

	except KeyError: #no data
		#set to default lead time of 2 weeks 
		leadtime = 0

	return leadtime


def sort(parts, Timestamps):
	"""
	Sort the data from api response to have just batch data.

	@params 
		- parts: data from api response/cache 
		- Timestamps: dictionary of timestamps for the four time periods used, and the current timestamp
					  timestamps are unix timestamps, in milliseconds represented as integers 
	@returns 
		- stock_list: dictionary of sorted data 
	"""
	part_entry = 0
	#create an empty dictionary to store all stock data 
	stock_list = {}

	#iterate through parts in data 
	#for each part get stock information and id 
	#create dictionary entries that holds all the IDs, Descriptions, and stock info 
	#append dictionary to list 
	for part in parts:
		add_part_flag = False; 

		#get wanted variables 
		part_id = parts[part_entry]["part/id"]
	
		try:
			part_description = parts[part_entry]["part/description"]
		except KeyError as e: #entry does not contain a description
			#added notes for exception, will only show if code is changed so exception is raised
			e.add_note(f"{part_id} does not contain the data field 'part/description'")
			part_description = None
		try:
			part_mpn = parts[part_entry]["part/mpn"]
		except KeyError as e: #entry does not contain an mpn
			part_mpn = None
			e.add_note(f"{part_id} does not contain the data field 'part/mpn'")
		try: 
			part_stock_count = parts[part_entry]["part/total_stock"]
		except KeyError as e: #entry does not contain a total stock count
			part_stock_count = None
			e.add_note(f"{part_id} does not contain the data field 'part/total_stock'")
		try:
			part_stock = parts[part_entry]["part/stock"]
		except KeyError as e:#entry does not contain a stock history
			part_stock = None
			e.add_note(f"{part_id} does not contain the data field 'part/stock'")
		try:
			part_restock = parts[part_entry]["date_last_restock"]
		except KeyError as e: 
			part_restock = None
			e.add_note(f"{part_id} does not contain the data field 'date_last_restock'")

		#there will always be a part lead since the update lead time function will add a default lead time if field is empty/doesnt exist 
		custom_fields = parts[part_entry]["part/custom-fields"]
		field_index = 0
		#loop through custom fields to find the lead time field
		for field in custom_fields:
			field_key = parts[part_entry]["part/custom-fields"][field_index]["key"]
			if field_key == "lead_time_(weeks)":
				part_lead_value = int(parts[part_entry]["part/custom-fields"][field_index]["value"])
			field_index += 1

		used_in = []

		#create dictionary of data feilds for parts
		stock_list[part_id] = {"description": part_description, 
							   "mpn": part_mpn, 
							   "total_stock": part_stock_count, 
							   "part/restock": part_restock, 
							   "lead_time_(weeks)": part_lead_value, 
							   "projects_used_in": used_in}

		#create empty list for valid stock entries for each part
		valid_stock = []
		#set stock entry counter to 0 for each part 
		stock_entry = 0
		
		#Loop through stock entries
		#Discard entries that have strings with 'move' in them
		#Discard postive entries 
		#Discard entries that do not have stock entries from the past year 
		for stock in part_stock:

			#set valid and negative flags 
			valid = True
			negative = False			
			#get stock data
			stock_data = parts[part_entry]["part/stock"][stock_entry]
			part_quantity = parts[part_entry]["part/stock"][stock_entry]["stock/quantity"]

			# check if stock update is for moving parts not production
			try:
				comment = parts[part_entry]["part/stock"][stock_entry]["stock/comments"]
				word = "moved"
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
			if valid and negative:
				valid_stock.append(stock_data)
				add_part_flag == True

			#increase stock counter 
			stock_entry += 1

		#add valid stock to stock list entries
		stock_list[part_id]["stock"] = valid_stock

		part_entry += 1

	return stock_list


def remove_empty_stock_list(parts):
	"""
	Remove entries in the sorted data that have no valid stock history. 

	@params 
		- parts: list of all parts data
	@returns 
		- refined_data: list of parts that have had valid stock history within the past year 
	"""	
	part_entry = 0 
	refined_data = []

	for part in parts: 
		data = parts[part_entry]
		valid = True

		try:
			stock_data = parts[part_entry]["part/stock"]
		except KeyError: #entry does not exist 
			valid = False

		if not stock_data:
			valid = False

		if valid: 
			refined_data.append(data) #add part entry to list if stock history is valid

		part_entry += 1 
		

	return refined_data


def remove_empty_stock_dict(sorted_stock):
	"""
	Remove entries in the sorted data that have no valid stock history. 

	@params 
		- sorted_stock: nested dictionary of valid part information 
	@returns 
		- refined_data: nested dictionary of parts that have had valid stock history within the past year 
	"""	
	refined_data = {}

	for part in sorted_stock: 
		data = sorted_stock[part]
		valid = True

		try:
			stock_data = sorted_stock[part]["stock"]
		except KeyError: #entry does not exist 
			valid = False

		if not stock_data:
			valid = False

		if valid: 
			refined_data[part] = data

	return refined_data


def get_data_for_airtable(sorted_stock):
	"""
	Sort data to be pushed to air table.

	@params
		- sorted_stock: nested dictionary containg data for all valid parts
	@returns 
		- airtable_data: airtable data for all parts, formatted as a list so it can be easily broken in to groups of 10 for pushing to airtable
	"""	
	airtable_data = []

	for part in sorted_stock: 
		part_id = part
		description = sorted_stock[part]["description"]
		mpn = sorted_stock[part]["mpn"]
		total_stock = sorted_stock[part]["total_stock"]
		last_batch = sorted_stock[part]["date_last_batch"]
		last_restock = sorted_stock[part]["part/restock"]
		risk = sorted_stock[part]["risk_level"]
		rop_estimate = int(sorted_stock[part]["estimated_rop"])
		leadtime = int(sorted_stock[part]["lead_time_(weeks)"])
		projects_used_in = sorted_stock[part]["projects_used_in"]

		#convert list to a string in order to push to airtable as a long text field 
		project_string = "\n".join(projects_used_in)

		entry = {"part_id": part_id,
				"description": description,
				"mpn": mpn,
				"total_stock": total_stock,
				"risk": risk,
				"lead_time_(weeks)": leadtime,
				"rop_estimate_(days)": rop_estimate, 
				"last_batch": last_batch,
				"last_restock": last_restock,
				"projects_used_in": project_string}

		data = {"fields": entry}

		airtable_data.append(data)

	return airtable_data


def get_group_of_ten(airtable_data):
	"""
	Prepare part data for pushing to airtable in groups of no more than 10.

	@params
		- airtable_data: list of parts left to be pushed to airtable
	@returns:
		- group_of_ten: list containing data for up to 10 parts
	"""	
	test_index = 0
	group_of_ten = []

	length = len(airtable_data)
	while test_index < 10 and test_index <= length - 1:
		group_of_ten.append(airtable_data.pop(0))
		test_index += 1

	return group_of_ten


TIME_PERIOD = 1 #time period in seconds (airtable is limited to 5 requests per second)	
@limits(calls = 5, period = TIME_PERIOD)
def push_to_airtable(airtable_data):
	"""
	limits decorator: ensures only 5 calls per second can be made, to meet the rate limit of airtables api 
	@params
		- calls: number of calls (integer) that can take place during one period 
		- period: time period (seconds)

	push_to_airtable function: 
	Pushes data to airtable for all valid parts. 
	
	Requires airtable base and table to be configured prior to runnning.
	All headers must match names and types of fields being pushed.
	headers and their types: 
		- part_id: single line text 
		- description: single line text
		- mpn: single line text
		- total_stock: number
		- risk: single line text
		- lead_time_(weeks): number
		- rop_estimate_(days): number
		- last_batch: date
		- last_restock: date
		- projects_used_in: long text

	@params
		- airtable_data: list of all data to be pushed to airtable 
	@returns: 
		- none
	"""
	length = len(airtable_data)
	number_of_calls = int(length / 10) + (length % 10 > 0) 
	print("pushing date to airtable")
	with alive_bar(number_of_calls, bar = "fish") as bar: #set up progress bar based off of number of calls to be made
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
			"Authorization": config["Authorization"],
			"Content-Type" : "application/json"
			}

			data = {}
			list_of_fields = ["part_id", "description"]
			entry = {"fieldsToMergeOn": list_of_fields}
			data = {"performUpsert": entry, "records": data_to_push}
			url = config["URL"] #store url in config file as url contains base and table IDs

			result = requests.patch(url, headers = headers, json = data)
			#print statement for testing 
			#print(result)

			bar() #update alive progress bar 


def get_projects(headers, current_timestamp):
	"""
	Get the list of projects from PartsBox or cache.

	@params 
		- headers: dictionary of headers with authorization key for api request
		- current_timestamp: timestamp from when get timestamps function was called 
	@returns 
		- result: dictionary with list of projects (list of dictionaries) from api response or cache and update flag to be used for getting project boms 
	"""	
	#get project data 
	url = "https://api.partsbox.com/api/1/project/all"
	
	cache_name = "project_cache.json"
	timeframe = "month"
	#see if cache needs to be updated
	update = cache.get_update_flag(current_timestamp, cache_name, timeframe)

	#check rate limit for Partsbox api
	check_partsbox_limit()

	#get data from cache or api response if necessary 
	data: dict = cache.fetch_data(update = update,
								  json_cache = cache_name,
								  url = url,
								  headers = headers, 
								  params = None)

	#get just data from api response
	projects = data["data"]

	result = {"projects": projects, "update": update}

	return result


def get_boms(projects, headers, update):
	"""
	Get boms for all projects from PartsBox or cache.

	@params
		- projects: list of dictionaries containing project data 
		- headers: dictionary of headers for api request, including api authroization key 
		- update: bool, set to True if projects cache was updated in get_projects, False otherwise
	@returns 
		- project_boms: list of dictionaries containing project names and their bom's (list of part IDs)
	"""	
	cache_name = "project_entries_cache.json"
	try:
		#cache is created 
		with open(cache_name, 'r') as file:
			json_data = json.load(file)
	except(FileNotFoundError, json.JSONDecodeError) as e:
		print(f'No local cache found... ({e})')
		json_data = None
 
	#create cache file 	
	if not json_data or update:
		number_of_calls = len(projects)
		print("getting boms from Partsbox")
		with alive_bar(number_of_calls, bar = "fish") as bar: #set up progress bar based off of number of calls to be made
			#make api requests in loop
			project_index = 0
			project_boms = []

			for project in projects: 
				#get project data
				project_name = projects[project_index]["project/name"]
				project_id = projects[project_index]["project/id"]
				
				#make api request 
				url = "https://api.partsbox.com/api/1/project/get-entries"	
				payload = {"project/id": project_id}

				#check rate limit for Partsbox api
				check_partsbox_limit()

				#get data from api response
				project_parts = requests.get(url, headers = headers, params = payload).json()
				project_parts = project_parts["data"]

				part_index = 0
				parts = []
				for part in project_parts:
					try:
						part_id = project_parts[part_index]["entry/part-id"] 
						parts.append(part_id)
					except KeyError as e: 
						e.add_note("part does not contain the data field 'entry/part-id'")

					part_index += 1

				bom_entry = {"project_name": project_name, "parts": parts}
				project_boms.append(bom_entry)

				project_index += 1
				bar()
		
			with open("project_entries_cache.json", "w") as file:
				json.dump(project_boms, file)

	else: #cache exists and does not need to be updated 
		print("Fetched data from local cache!")
		project_boms = json_data 

	return project_boms


def update_project_data(project_boms, sorted_stock): 
	"""
	Goes through project boms and adds project names to parts. 

	@params
		- project_boms: list of dictionary entries consisiting of project names and bom's (list of part IDs)
		- sorted_stock: nested dictionary containg data for all valid parts
	@returns
		- sorted_stock: nested dictionary containg data for all valid parts with added data for projects which parts are used in 
	"""	
	project_index = 0 

	for project in project_boms: 
		part_index = 0 
		parts = project_boms[project_index]["parts"]
		project_name = project_boms[project_index]["project_name"]

		for part in parts:
			try: 
				part_id = parts[part_index]
				sorted_stock[part_id]["projects_used_in"].append(project_name)
			except KeyError as e:
				e.add_note(f"{part_id} was not found in sorted_stock")

			part_index += 1 

		project_index += 1

	return sorted_stock