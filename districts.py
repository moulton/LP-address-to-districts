import csv
import string
import json
import urllib, urllib.request, urllib.parse
import time


# Documentation for files and APIs used:
# Google geocode API documentation
#	https://developers.google.com/maps/documentation/geocoding/
# FCC census block api documentation
#	http://www.fcc.gov/developers/census-block-conversions-api
# Virginia legislative districts
#	http://redistricting.dls.virginia.gov/2010/RedistrictingPlans.aspx#31
#	http://redistricting.dls.virginia.gov/2010/RedistrictingPlans.aspx#27
#	http://redistricting.dls.virginia.gov/2010/RedistrictingPlans.aspx#28
# Census districts
#	http://www.census.gov/geo/maps-data/data/baf_description.html
#	http://www.census.gov/geo/maps-data/data/baf.html
#	http://www.census.gov/geo/maps-data/data/nlt_description.html
#	http://www.census.gov/geo/maps-data/data/nlt.html
#	http://www.census.gov/geo/maps-data/data/gazetteer2010.html

# SORRY MY CODE IS SO MESSY.  THIS IS AN ALPHA RELEASE.
#
# How to use:
#
# All you need to download is block assignment files and name lookup tables for your state (see above).
# For congress, state upper, and state lower I found that redistricting plans from Virginia were more accurate
# than the Census files, but that was right after redistricting.  By now they're probably equivalent.
#
# Download the files for your state, put them in a folder called "data", and change the file names below.
#
# Input is a tab delimited file with field names at the top and data in the rest of the rows.
#
# I had to breakup the national or state data dump into separate files for members, lapsed, and inquiries,
# then further separate it into chunks less than 2500 records (max Google lookups / day).
# Run the files every 24+ hours until you get through your state database.
#
# Note: It may take about 45 minutes per run because I put a 1 second delay for each lookup.
#
# There is an output file and an error file, which catches any records that didn't process correctly.
# Check the error file when complete to try to figure out the problem.  Sometimes just re-running those records works.
# Other times there is an obvious pattern to errors (e.g., an apostrophe in the name, a P.O. Box, etc.).
#
# Sorry, I won't be able to provide much support until late-August.
#
# Areas I want to improve the program:
# 1) Make it input the data dump, break it up into member/lapsed/inquiries, break it up into 2500 chunks,
#    and re-assemble after completion.
# 2) Put phone numbers / email addresses in logical fields instead of all over the place (old dump format).
# 3) Deal better with situations where geocoding returns more than 1 record (it just takes the first now).
# 4) Make it work by just plugging in the state one place rather than making each state edit the data file names.

# variables (factored out so you only need to change things one place if data dump format or API changes)
# filenames
fn_input =			'members-2014-06-22.txt'
fn_output =			'members-2014-06-22-districts.txt'
fn_error =			'members-2014-06-22-error.txt'
fn_congress =			'data\\HB251_bell_blkassign.txt'
fn_senate =			'data\\HB5005_passed_042811_senateplan.txt'
fn_house =			'data\\hb5005_passed_042811_houseplan.txt'
fn_county =			'data\\counties_list_51.txt'
fn_place =			'data\\BlockAssign_ST51_VA_INCPLACE_CDP.txt'
fn_incorporated =		'data\\NAMES_ST51_VA_INCPLACE.txt'
fn_CDP =			'data\\NAMES_ST51_VA_CDP.txt'
fn_school_number =		'data\\BlockAssign_ST51_VA_SDUNI.txt'
fn_school =			'data\\NAMES_ST51_VA_SDUNI.txt'
fn_precinct_number =		'data\\BlockAssign_ST51_VA_VTD.txt'
fn_precinct =			'data\\NAMES_ST51_VA_VTD.txt'

# database fields
db_member_id =			'CnBio_ID'
db_last_name =			'CnBio_Last_Name'
db_street_address =		'CnAdrPrf_Addrline1'
db_city =			'CnAdrPrf_City'
db_state =			'CnAdrPrf_State'
db_zip =			'CnAdrPrf_ZIP'
db_congress =			'Local_Congress'
db_senate =			'Local_StateUpperDistrict'
db_house =			'Local_StateLowerDistrict'
db_county =			'Local_County'
db_county_subdivision =		'Local_CountyDistrict'
db_incorporated =		'Local_CityDistrict'
db_CDP =			'Local_CensusDesignatedPlace'
db_school =			'Local_SchoolDistrict'
db_precinct =			'Local_Precinct'
db_precinct_number =		'Local_PrecinctNumber'
db_fips =			'FIPS'
db_latitude =			'Latitude'
db_longitude =			'Longitude'
db_gg_status =			'GG_Status'
db_gg_results =			'GG_Results'
db_gg_type =			'GG_Type'
db_gg_formatted_address =	'GG_Formatted_Address'
db_fcc_status =			'FCC_Status'

# variables populated by this script
db_districts = [
				db_congress,
				db_senate,
				db_house,
				db_county,
				db_county_subdivision,
				db_incorporated,
				db_CDP, db_school,
				db_precinct,
				db_precinct_number,
				db_fips,
				db_latitude,
				db_longitude,
				db_gg_status,
				db_gg_results,
				db_gg_type,
				db_gg_formatted_address,
				db_fcc_status
]

# assignment database fields
assign_lookup_fields = [ db_senate, db_house, db_incorporated, db_school, db_precinct ]

# Google geocode API
gg_base_URI =			'http://maps.googleapis.com/maps/api/geocode/json'
gg_status_valid =		[ 'OK' ]
gg_status_invalid =		[ 'ZERO_RESULTS', 'REQUEST_DENIED', 'INVALID_REQUEST' ]
gg_status_retry =		[ 'OVER_QUERY_LIMIT', 'UNKNOWN_ERROR' ]
gg_types_valid =		[ 'street_address', 'subpremise' ]
gg_status =			'status'
gg_results =			'results'
gg_types =			'types'
gg_formatted_address =		'formatted_address'
gg_geometry =			'geometry'
gg_location =			'location'
gg_latitude =			'lat'
gg_longitude =			'lng'
gg_address_components =		'address_components'
gg_ac_long =			'long_name'
gg_ac_short =			'short_name'
gg_ac_types =			'types'
gg_county_subdivision =		'administrative_area_level_3'

# FCC API
fcc_base_URI =			'http://data.fcc.gov/api/block/find'
fcc_status =			'status'
fcc_block =			'Block'
fcc_fips =			'FIPS'
fcc_census_year =		'2010'
fcc_status_valid =		[ 'OK' ]

# create empty global header fields and hash tables
fields_input =			[]
fields_output =			[]


# open output files
output_file = open( fn_output, 'w' )
error_file = open( fn_error, 'w' )


# function to populate a hash table
# assume 1st field is key, 2nd field is value, the file has headers, and the file is tab delimited
def populate_lookup( fn_lookup, keys=[1], values=[2], header=True, dialect='excel-tab', delimiter=',' ):
	lookup = {}
	# The fieldnames part basically creates field names that are number strings '1' '2' '3' etc.
	# up to the highest number field used as a key or value.
	for line_number, line in enumerate( csv.DictReader( open( fn_lookup, 'r' ), fieldnames=list( map( str, range( 1, max( keys + values ) + 1 ) ) ), restval='x', dialect=dialect, delimiter=delimiter ) ):
		if line_number or not header:
			key_merge = []
			value_merge = []
			for key in keys:
				key_merge.append( line[ str( key ) ] )
			for value in values:
				value_merge.append( line[ str( value ) ] )
			lookup[ ''.join( key_merge ) ] = ''.join( value_merge )
	return lookup


# populate hash tables

# populate U.S. Congress hash table
# 	key is 15 digit FIPS
# 	value is district
lookup_congress =		populate_lookup( fn_congress, header=False, delimiter=',' )

# populate State Senate hash table
# 	key is 15 digit FIPS
# 	value is district
lookup_senate =			populate_lookup( fn_senate, header=False, delimiter=',' )

# populate House of Delegates hash table
# 	key is 15 digit FIPS
# 	value is district
lookup_house =			populate_lookup( fn_house, header=False, delimiter=',' )

# populate County hash table
# 	key is 2 digit state FIPS + 3 digit county FIPS
# 	value is county name
lookup_county =			populate_lookup( fn_county, [ 2 ], [ 4 ], delimiter='\t' )

# populate Place hash table (later fed into Incorporated Place and Census Designated Place)
# 	key is 15 digit FIPS
# 	value is 5 digit place FIPS
lookup_place =			populate_lookup( fn_place )

# populate Incorporated Place hash table
# 	key is 2 digit state FIPS + 5 digit place FIPS
# 	value is incorporated place name
lookup_incorporated =		populate_lookup( fn_incorporated, [ 1, 2 ], [ 3 ], delimiter='|' )

# populate Census Designated Place hash table
# 	key is 2 digit state FIPS + 5 digit place FIPS
# 	value is census designated place name
lookup_CDP =			populate_lookup( fn_CDP, [ 1, 2 ], [ 3 ], delimiter='|' )

# populate School Number hash table
# 	key is 15 digit FIPS
# 	value is 5 digit school FIPS
lookup_school_number =		populate_lookup( fn_school_number, delimiter=',' )

# populate School hash table
# 	key is 2 digit state FIPS + 5 digit school FIPS
# 	value is school name
lookup_school =			populate_lookup( fn_school, [ 1, 2 ], [ 3 ], delimiter='|' )

# populate Precinct Number hash table
# 	key is 15 digit FIPS
# 	value is 3 digit precinct number
#	(middle field is county, which we already have)
lookup_precinct_number =	populate_lookup( fn_precinct_number, [ 1 ], [ 3 ], delimiter=',' )

# populate Precinct hash table
# 	key is 2 digit state FIPS + 3 digit county FIPS + 3 digit precinct number
# 	value is precinct name
lookup_precinct =		populate_lookup( fn_precinct, [ 1, 2, 3 ], [ 4 ], delimiter='|' )


# read in list of header fields (need to specify field names in a particular order in the next for loop)
for line in csv.reader( open( fn_input, 'r' ), dialect='excel-tab' ):
	fields_input = line
	break

# iterate through lines in the input file
for line_number, line in enumerate( csv.DictReader( open( fn_input, 'r' ), fieldnames=fields_input, dialect='excel-tab' ) ):
	# empty values in districts disctionary
	districts = dict.fromkeys( db_districts, '' )
	db_place = ''
	db_school_number = ''
	
	# slightly different for the header line (line 0)
	if not line_number:
		# figure out which header fields are new (to be added)
		new_fields = db_districts
		for field in fields_input:
			if field in new_fields:
				new_fields.remove( field )
		# add on new header fields (for data generated by this script)
		fields_output = fields_input + new_fields
		# output the header fields separated by a tab
		output_file.write( '\t'.join( fields_output ) + '\n' )
	
	# for each of the non-header lines in the file do this stuff
	else:
		# wait a second to be nice to the Google geocode API
		time.sleep(1)
		# form the Google geocode API query
		gg_address = ' '.join( [ line[ db_street_address ], line[ db_city ], line[ db_state ], line[ db_zip ] ] )
		gg_params = { 'sensor' : 'false', 'address' : gg_address }
		gg_request = urllib.request.Request( gg_base_URI + '?' + urllib.parse.urlencode( gg_params, doseq=True ) )
		while True:
			# submit the Google geocode API query
			gg_response = urllib.request.urlopen( gg_request )
			gg_data = json.loads( gg_response.read().decode(), parse_float=str )
			districts[ db_gg_status ] = gg_data[ gg_status ]
			# check the status of the Google geocode API query
			# if the status is valid, don't retry
			if districts[ db_gg_status ] in gg_status_valid:
				break
			# if the status is invalid, write out an error message and don't retry
			elif districts[ db_gg_status ] in gg_status_invalid:
				error_file.write( 'GG FAILURE:' + '\t' + districts[ db_gg_status ] + '\t' + line[ db_member_id ] + '\t' + line[ db_last_name ] + '\n' )
				break
			# if the status can be remedied, write out an error message and retry
			else:
				error_file.write( 'GG FAILURE:' + '\t' + districts[ db_gg_status ] + '\t' + line[ db_member_id ] + '\t' + line[ db_last_name ] + '\n' )
				# wait 1800 seconds to be nice to the Google geocode API
				time.sleep(1800)
				continue
		
		# check if the Google API status is valid
		if districts[ db_gg_status ] in gg_status_valid:
			# read in the data
			districts[ db_gg_results ] = str( len( gg_data[ gg_results ] ) )
			for db_gg_result in gg_data[ gg_results ]:
				if not len( db_gg_result[ gg_types ] ):
					error_file.write( 'GG FAILURE:' + '\t' + 'empty types' + '\t' + line[ db_member_id ] + '\t' + line[ db_last_name ] + '\n' )
					continue
				districts[ db_gg_type ] = db_gg_result[ gg_types ][ 0 ]
				if districts[ db_gg_type ] in gg_types_valid:
					districts[ db_gg_formatted_address ] = db_gg_result[ gg_formatted_address ]
					districts[ db_latitude ]= db_gg_result[ gg_geometry ][ gg_location ][ gg_latitude ]
					districts[ db_longitude ] = db_gg_result[ gg_geometry ][ gg_location ][ gg_longitude ]
					# get County Subdivision (magisterial district)
					for db_gg_address_component in db_gg_result[ gg_address_components ]:
						if gg_county_subdivision in db_gg_address_component[ gg_ac_types ]:
							districts[ db_county_subdivision ] = db_gg_address_component[ gg_ac_long ]
					break
				else:
					error_file.write( 'GG FAILURE:' + '\t' + districts[ db_gg_type ] + '\t' + line[ db_member_id ] + '\t' + line[ db_last_name ] + '\n' )
					continue		
		# check if the Google API type is valid (types that will give precise geocodes: longitude & latitude)
		if districts[ db_gg_type ] in gg_types_valid:
			# form the FCC API query
			fcc_params = { 'latitude' : districts[ db_latitude ], 'longitude' : districts[ db_longitude ], 'censusYear' : fcc_census_year, 'format' : 'json', 'showall' : False }
			fcc_request = urllib.request.Request( fcc_base_URI + '?' + urllib.parse.urlencode( fcc_params, doseq=True ) )
			# submit the FCC API query
			fcc_response = urllib.request.urlopen( fcc_request )
			fcc_data = json.loads( fcc_response.read().decode() )
			districts[ db_fcc_status ] = fcc_data[ fcc_status ]
			# check the status of the FCC API query
			# if the status is valid, get the FIPS
			if districts[ db_fcc_status ] in fcc_status_valid:
				# FIPS (Federal Information Processing Standard) is a 15 digit census code:
				# 2-digit State code, 3-digit County code, 6-digit census tract code, 4 digit block code
				districts[ db_fips ] = fcc_data[ fcc_block ][ fcc_fips ]
			# if the status is invalid, write out an error message
			else:
				error_file.write( 'FCC FAILURE:' + '\t' + districts[ db_fcc_status ] + '\t' + line[ db_member_id ] + '\t' + line[ db_last_name ] + '\n' )
		
		# check if there is a FIPS
		if districts[ db_fips ]:
			# lookup the U.S. Congress district
			# 	key is 15 digit FIPS
			if districts[ db_fips ] in lookup_congress:
				districts[ db_congress ] = lookup_congress[ districts[ db_fips ] ]
			# lookup the State Senate district
			# 	key is 15 digit FIPS
			if districts[ db_fips ] in lookup_senate:
				districts[ db_senate ] = lookup_senate[ districts[ db_fips ] ]
			# lookup the House of Delegates district
			# 	key is 15 digit FIPS
			if districts[ db_fips ] in lookup_house:
				districts[ db_house ] = lookup_house[ districts[ db_fips ] ]
			# lookup the County
			# 	key is 2 digit state FIPS + 3 digit county FIPS (start of 15 digit FIPS)
			if districts[ db_fips ][:5] in lookup_county:
				districts[ db_county ] = lookup_county[ districts[ db_fips ][:5] ]
			# lookup the County Subdivision
			# 	Note: County Subdivision was already extracted from the Google geocode API
			# lookup the Place
			# 	key is 15 digit FIPS
			if districts[ db_fips ] in lookup_place:
				db_place = lookup_place[ districts[ db_fips ] ]
			# lookup the Incorporated Place
			# 	key is 2 digit state FIPS + 5 digit place FIPS
			if ''.join( [ districts[ db_fips ][:2], db_place ] ) in lookup_incorporated:
				districts[ db_incorporated ] = lookup_incorporated[ ''.join( [ districts[ db_fips ][:2], db_place ] ) ]
			# lookup the Census Designated Place
			# 	key is 2 digit state FIPS + 5 digit place FIPS
			if ''.join( [ districts[ db_fips ][:2], db_place ] ) in lookup_CDP:
				districts[ db_CDP ] = lookup_CDP[ ''.join( [ districts[ db_fips ][:2], db_place ] ) ]
			# lookup the School Number
			# 	key is 15 digit FIPS
			if districts[ db_fips ] in lookup_school_number:
				db_school_number = lookup_school_number[ districts[ db_fips ] ]
			# lookup the School
			# 	key is 2 digit state FIPS + 5 digit school FIPS
			if ''.join( [ districts[ db_fips ][:2], db_school_number ] ) in lookup_school:
				districts[ db_school ] = lookup_school[ ''.join( [ districts[ db_fips ][:2], db_school_number ] ) ]
			# lookup the Precinct Number
			# 	key is 15 digit FIPS
			if ( districts[ db_fips ] ) in lookup_precinct_number:
				districts[ db_precinct_number ] = lookup_precinct_number[ districts[ db_fips ] ]
			# lookup the Precinct
			# 	key is 2 digit state FIPS + 3 digit county FIPS (start of 15 digit FIPS) + 3 digit precinct number
			if ''.join( [ districts[ db_fips ][:5], districts[ db_precinct_number ] ] ) in lookup_precinct:
				districts[ db_precinct ] = lookup_precinct[ ''.join( [ districts[ db_fips ][:5], districts[ db_precinct_number ] ] ) ]
		
		# output a line of data
		output_line = []
		for field in fields_output:
			# output districts
			if field in districts:
				output_line.append( districts[ field ] )
			# otherwise, output data directly from the input
			else:
				output_line.append( line[ field ])
		# separate with tabs
		output_file.write( '\t'.join( output_line ) + '\n' )

# close the files
output_file.close()
error_file.close()
