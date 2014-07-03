LP-address-to-districts
=======================

Adds districts (congress down to precinct) to Libertarian Party state data dumps.

Documentation for files and APIs used:

Google geocode API documentation
* https://developers.google.com/maps/documentation/geocoding/

FCC census block api documentation
* http://www.fcc.gov/developers/census-block-conversions-api

Virginia legislative districts
* http://redistricting.dls.virginia.gov/2010/RedistrictingPlans.aspx#31
* http://redistricting.dls.virginia.gov/2010/RedistrictingPlans.aspx#27
* http://redistricting.dls.virginia.gov/2010/RedistrictingPlans.aspx#28

Census districts
* http://www.census.gov/geo/maps-data/data/baf_description.html
* http://www.census.gov/geo/maps-data/data/baf.html
* http://www.census.gov/geo/maps-data/data/nlt_description.html
* http://www.census.gov/geo/maps-data/data/nlt.html
* http://www.census.gov/geo/maps-data/data/gazetteer2010.html

How to use:

All you need to download is block assignment files and name lookup tables for your state (see above).  For congress, state upper, and state lower I found that redistricting plans from Virginia were more accurate than the Census files, but that was right after redistricting.  By now they're probably equivalent.

Download the files for your state, put them in a folder called "data", and change the file names below.

Input is a tab delimited file with field names at the top and data in the rest of the rows.

I had to breakup the national or state data dump into separate files for members, lapsed, and inquiries, then further separate it into chunks less than 2500 records (max Google lookups / day). Run the files every 24+ hours until you get through your state database.

Note: It may take about 45 minutes per run because I put a 1 second delay for each lookup.

There is an output file and an error file, which catches any records that didn't process correctly. Check the error file when complete to try to figure out the problem.  Sometimes just re-running those records works.  Other times there is an obvious pattern to errors (e.g., an apostrophe in the name, a P.O. Box, etc.).

Sorry, I won't be able to provide much support until late-August.

Areas I want to improve the program:
* 1) Make it input the data dump, break it up into member/lapsed/inquiries, break it up into 2500 chunks, and re-assemble after completion.
* 2) Put phone numbers / email addresses in logical fields instead of all over the place (old dump format).
* 3) Deal better with situations where geocoding returns more than 1 record (it just takes the first now).
* 4) Make it work by just plugging in the state one place rather than making each state edit the data file names.
