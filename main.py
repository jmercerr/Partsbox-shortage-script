""" 
Main module for partsbox api interface
"""

import json 
import requests 
import sort_data
import calculate
import time_stamp
import cache


"""
function to format the printing of json data
@params
	- obj: object containing json data
@returns 
	- none
"""
def jprint(obj):
	text = json.dumps(obj, indent = 4, default = str)
	print(text)


"""main"""
if __name__ == '__main__':
	url = 'https://api.partsbox.com/api/1/part/all' 
	json_cache = 'request_cache.json'

	try: 
		with open("config.json") as config_file: 
			config = json.load(config_file)
	except FileNotFoundError: 
		print("no config file found")
		f = open("config.json", "x")
		f.close
		print("config.json file created, populate file with your api key and rerun program!\n the format for the config file is as follows\n {'API_key': 'APIKey enter_your_api_key_here'}")

	headers = {
	'Authorization': config["API_key"] 
	}

	#for testing timestamp function 
	print("entering timestmap function")
	Timestamps = time_stamp.get_timestamps()
	print(Timestamps)
	print("after timestamp function")

	update = cache.get_update_flag(Timestamps[0])
	print(update)


	data: dict = cache.fetch_data(update=update,
						    json_cache=json_cache,
							url=url, 
							headers=headers)

	#create list of just the data entries from api response
	parts = data['data']


	#for testing delete empty stock lists 
	print("before delete function")
	parts = sort_data.remove_empty_stock_list(parts)
	#jprint(sorted_stock)
	length = len(parts)
	print('Length after inital delete', length)
	print("after delete function")


	#for testing total stock function
	print("entering total stock function")
	parts = calculate.total_stock(parts)
	#jprint(parts)
	print("after stock function")


	#for testing date of last restock function 
	print("before get last restock function")
	time_stamp.get_date_of_last_restock(Timestamps[0], parts)
	#jprint(parts)
	print("after get last restock function")


	#for testing sort function
	print("before sort function")
	sorted_stock = sort_data.sort(parts, Timestamps)
	#jprint(sorted_stock)
	print("after sort function")


	#for testing delete empty stock lists 
	print("before delete function")
	length = len(sorted_stock)
	print("length before second delete", length)
	sorted_stock = sort_data.remove_empty_stock_dict(sorted_stock)
	#jprint(sorted_stock)
	length = len(sorted_stock)
	print('Length after second delete', length)
	print("after delete function")


	#for testing batch average function 
	print("before batch avg function")
	batch_averages = calculate.get_avg_batch(sorted_stock, Timestamps)
	#jprint(batch_averages)
	print("after batch avg function")


	#for testing average time function 
	print("before time average function")
	sorted_stock = calculate.get_avg_time(sorted_stock, Timestamps)
	#jprint(sorted_stock)
	print("after time average function")


	#for testing time since last batch function 
	print("before time since function")
	sorted_stock = time_stamp.get_time_since_last_batch(Timestamps[0], sorted_stock)
	#jprint(sorted_stock)
	print("after time since function")


	#testing lead time function
	'''
	file_name = input("Enter the name of the CSV that contains lead times: ")#get input from user for file name
	if file_name == "": #no file name provided
		calculate.get_lead_times(sorted_stock)
	else: #file name provided
		calculate.get_lead_times(sorted_stock, file_name)
	'''
	calculate.get_lead_times(sorted_stock)
	#jprint(sorted_stock)


	#for testing risk level function 
	print("before risk level function")
	sorted_stock = calculate.get_risk_level(sorted_stock, Timestamps[0])
	#jprint(sorted_stock)
	print("after risk level function")


	print("before creating json file")
	json_data = sort_data.get_data_for_airtable(sorted_stock, 0)
	print("after creating json file")

	jprint(json_data)
