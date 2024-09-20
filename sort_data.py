"""
Module that contains functions for sorting data for partsbox api interface 
"""


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
	part_entry=0

	#create an empty list to store all stock data 
	stock_list = []

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
		except KeyError:
			part_description = None
		try:
			part_mpn = parts[part_entry]['part/mpn']
		except KeyError:
			part_mpn = None
		try: 
			part_stock_count = parts[part_entry]['part/total_stock']
		except KeyError:
			part_stock_count = None
		try:
			part_stock = parts[part_entry]['part/stock']
		except KeyError:
			part_stock = None

		#create dictionary of data feilds for parts
		entry = {'id': part_id, 'description': part_description, 'mpn': part_mpn, 'total_stock': part_stock_count}

		#add part data to stock list 
		stock_list.append(entry)

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
			except KeyError:
				pass
			try: 
				stock_timestamp = parts[part_entry]['part/stock'][stock_entry]['stock/timestamp']
			except KeyError: 
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
		stock_list[part_entry]['stock'] = valid_stock

		#increase part counter
		part_entry = part_entry + 1

	return stock_list



'''
function to remove entries in the sorted data that have no valid stock history 
@params 
	- json_data: json data for parts 
	- stock_key: string for accessing stock data either 'part/stock' or 'stock'. depends on type of json data being passed 
@returns 
	- refined_stock: list of parts that have had valid stock history within the past year 
'''
def remove_empty_stock(json_data, stock_key):
	part_entry = 0 
	refined_data = []

	for part in json_data: 
		data = json_data[part_entry]
		valid = True

		try:
			stock_data = json_data[part_entry][stock_key]
		except KeyError:
			valid = False

		if stock_data == []:
			valid = False

		if valid == True: 
			refined_data.append(data) #add part entry to list if stock history is valid

		part_entry += 1 

	return refined_data
	
