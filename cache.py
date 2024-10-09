'''
module that contains functions for creating an updating the json cache file

'''

import json 
import requests 
import time 
import os

'''
function determines if cache file exists 
	if file exists - use data from file
	else - creates cache file, makes api request, stores response in file 
@params
	- update: flag
	- json_cache: file name
	- url: for api request
	- headers: for api request
@returns
	- json_data: data in the cache file 
'''
def fetch_data(*, update: bool = False, json_cache: str, url: str, headers: dict, params: dict):
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
		if params != None:
			json_data = requests.get(url, headers=headers, params=params).json()
		else:
			json_data = requests.get(url, headers=headers).json()


		with open(json_cache, 'w') as file:
			json.dump(json_data, file)

	return json_data


'''
function determines if cache file needs to be updated with new data from partsbox
@params
	- current_timestamp: the timestamp from when the get_timestamps function was called treated as current time
@returns 
	- update: bool flag (set to true if the cache was last modified over a week ago, false otherwise)
'''
def get_update_flag(current_timestamp, cache): 
	MILLI_PER_WEEK = 604800000

	#get timestamp in seconds
	modified_time = int(os.path.getmtime(cache))

	#convert to milliseconds 
	modified_time = modified_time * 1000

	one_week_ago = current_timestamp - MILLI_PER_WEEK
	#testing
	#one_week_ago = current_timestamp

	if modified_time >= one_week_ago: #modified within the past week 
		update = False
	else: #modified more than a week ago
		update = True

	return update




