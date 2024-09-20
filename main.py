""" 
Main module for partsbox api interface
"""

import json 
import requests 
import sort_data
import calculate
import time_stamp


"""function determines if cache file exists 
	if file exists - use data from file
	else - creates cache file, makes api request, stores response in file 
@params
	- update: flag
	- json_cache: file name
	- url: for api request
	- headers: for api request
@returns
	- json_data: data in the cache file 
"""
def fetch_data(*, update: bool = False, json_cache: str, url: str, headers: dict):
	if update:
		json_data = None
	else:
		try:
			#cache is created 
			with open(json_cache, 'r') as file:
				json_data = json.load(file)
				print('Fetched data from local cache!')
		except(FileNotFoundError, json.JSONDecodeError) as e:
			print(f'No local cache found... ({e})')
			json_data = None

	#create cache file 
	if not json_data:
		print('Fetching new json data... (creating local cache)')
		json_data = requests.get(url, headers=headers).json()

		with open(json_cache, 'w') as file:
			json.dump(json_data, file)

	return json_data


"""
function to format the printing of json data
@params
	- obj: object containing json data
@returns 
	- none
"""
def jprint(obj):
	text = json.dumps(obj, indent = 4)
	print(text)


"""main"""
if __name__ == '__main__':
	url = 'https://api.partsbox.com/api/1/part/all' 
	json_cache = 'request_cache.json'

	with open("config.json") as config_file: 
		config = json.load(config_file)

	headers = {
	'Authorization': config["API_key"] 
	}

	data: dict = fetch_data(update=False,
						    json_cache=json_cache,
							url=url, 
							headers=headers)

	#create list of just the data entries from api response
	parts = data['data']

	#for testing timestamp function 
	print("entering timestmap function")
	Timestamps = time_stamp.get_timestamps()
	print(Timestamps)
	print("after timestamp function")


	#for testing delete empty stock lists 
	print("before delete function")
	parts = sort_data.remove_empty_stock(parts, 'part/stock')
	#jprint(sorted_stock)
	length = len(parts)
	print('Length after inital delete', length)
	print("after delete function")


	#for testing total stock function
	print("entering total stock function")
	parts = calculate.total_stock(parts)
	#jprint(parts)
	print("after stock function")


	#for testing sort function
	print("before sort function")
	sorted_stock = sort_data.sort(parts, Timestamps)
	#jprint(sorted_stock)
	print("after sort function")


	#for testing delete empty stock lists 
	print("before delete function")
	sorted_stock = sort_data.remove_empty_stock(sorted_stock, 'stock')
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


	#for testing risk level function 
	print("before risk level function")
	sorted_stock = calculate.get_risk_level(sorted_stock, Timestamps[0])
	jprint(sorted_stock)
	print("after risk level function")
