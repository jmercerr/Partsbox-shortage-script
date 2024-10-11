""" 
Main module for partsbox api interface.

"""

import json 
import requests 
import sort_data
import calculate
import time_stamp
import cache


#constants for indexing into partsbox config list
WRITE = 0
READ = 1


def jprint(obj):
	"""
	Format the printing of json data (for testing).

	@params
		- obj: object containing json data
	@returns 
		- none
	"""
	text = json.dumps(obj, indent = 4, default = str)
	print(text)


"""main"""
if __name__ == '__main__':
	#get all parts data from PartsBox
	url = "https://api.partsbox.com/api/1/part/all" 
	json_cache = "request_cache.json"

	try: 
		with open("partsbox_config.json") as config_file: 
			config = json.load(config_file)
	except FileNotFoundError: 
		print("no config file found")
		f = open("partsbox_config.json", "x")
		f.close
		print("partsbox_config.json file created, populate file with your api key and rerun program!\n the format for the config file is as follows\n {'API_key': 'APIKey enter_your_api_key_here'}")

	headers = {
	"Authorization": config[READ]["API_key"],
	"Content-Type" : "application/json" #get api key for read only access
	}

	#for testing timestamp function 
	print("entering timestmap function")
	Timestamps = time_stamp.get_timestamps()
	print("after timestamp function")
	cache_name = "request_cache.json"
	timeframe = "week"

	update = cache.get_update_flag(Timestamps[0], cache_name, timeframe)

	#check rate limit for Partsbox api
	sort_data.check_partsbox_limit()

	data: dict = cache.fetch_data(update = update,
						    json_cache = json_cache,
							url = url, 
							headers = headers,
							params = None)

	#create list of just the data entries from api response
	parts = data["data"]


	#for testing delete empty stock lists 
	print("before delete function")
	parts = sort_data.remove_empty_stock_list(parts)
	#jprint(sorted_stock)
	length = len(parts)
	print("Length after inital delete", length)
	print("after delete function")


	#for testing lead time function 
	print("entering update lead time functions")
	#change header to api key for writing in order to update lead times if necessary 
	headers = {
			"Authorization": config[WRITE]["API_key"] 
			}
	sort_data.update_lead_times(parts, headers)
	print("after update lead time function")


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
	print("Length after second delete", length)
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
	#jprint(sorted_stock)
	print("after risk level function")

	#for testing get projects function
	print("before getting projects")
	result = sort_data.get_projects(headers, Timestamps[0])
	projects = result["projects"]
	update = result["update"]
	#jprint(projects)
	print("after getting projects")

	#for testing getting boms 
	print("before getting boms")
	project_boms = sort_data.get_boms(projects, headers, update)
	#jprint(project_boms)
	print("after getting boms")

	#for testing the update project data 
	print("before updating project data")
	sorted_stock = sort_data.update_project_data(project_boms, sorted_stock)
	#jprint(sorted_stock)
	print("after updating project data")


	#for testing the get data for airtable function
	print("before getting data for airtable")
	airtable_data = sort_data.get_data_for_airtable(sorted_stock)
	print("after getting data for airtable")
	#jprint(airtable_data) 


	#for testing pushing to airtable
	print("before pushing to airtable")
	sort_data.push_to_airtable(airtable_data)
	print("after pushing to airtable")