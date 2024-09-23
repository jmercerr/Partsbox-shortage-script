'''
module that contains functions for creating an updating the json cache file

'''

import json 
import requests 


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