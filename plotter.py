# covid-19 nyt data plotter

import numpy as np
from scipy import interpolate
from scipy import optimize
from matplotlib import pyplot as plt
from matplotlib import dates
from textwrap import wrap
import datetime as dt
from datetime import timedelta
import urllib.request
import re
import sys
import csv
import os
from typing import Dict, List
from enum import Enum
import us

import requests
from requests_ntlm import HttpNtlmAuth

class PlotType(Enum):
	CASES = 1
	DEATHS = 2
	CASES_1000 = 3
	DEATHS_1000 = 4
	CASES_GRADIENT = 5
	DEATHS_GRADIENT = 6
	CASES_DOUBLING = 7
	CASES_1000_GRADIENT = 8
	DEATHS_1000_GRADIENT = 9
	COVID_TRACKING_KEY = 10
	COVID_TRACKING_KEY_1000 = 11

FIPS_INVALID = -3

def get_path() -> str:
	return os.path.join(os.getcwd(), "Data")

def get_file_name() -> str:
	return os.path.join(get_path(), "us-counties.csv")

def get_file_name_ww() -> str:
	return os.path.join(get_path(), "ww.csv")
	
def get_file_name_covid_tracking() -> str:
	return os.path.join(get_path(), "covid_tracking_states_daily.csv")

def download_csv(url: str, file_name: str, ntlm_auth: bool):
	html = ""
	if ntlm_auth:
		r = requests.get(url, auth=HttpNtlmAuth(":",":"))
		html = r.text
	else:
		html = urllib.request.urlopen(url).read().decode("utf-8")
	path = get_path()
	if not os.path.exists(path):
		os.mkdir(path)
	file = open(file_name, "w")
	file.write(html)
	file.close()

def match_region(fips: int, abbr: str, state: bool, row: Dict[str, str]) -> bool:
	if state:
		return row['state'] == abbr
	if 'geo' in row:
		return row['geo'] == abbr
	if not row['fips']:
		return row['county'] == "New York City" and fips == -1
	return int(row['fips']) == fips

def needs_wikipedia_citation(fips: int, state: bool, type: PlotType) -> bool:
	if fips <= FIPS_INVALID and not state:
		return False
	return plot_type == PlotType.CASES_1000 or \
		plot_type == PlotType.DEATHS_1000 or \
		plot_type == PlotType.CASES_1000_GRADIENT or \
		plot_type == PlotType.DEATHS_1000_GRADIENT or \
		plot_type == PlotType.COVID_TRACKING_KEY_1000
		
def is_covid_tracking_type(type: PlotType) -> bool:
	return plot_type == PlotType.COVID_TRACKING_KEY or \
		plot_type == PlotType.COVID_TRACKING_KEY_1000

def build_wikipedia_url(fips: int, abbr: str, rows: List[Dict[str, str]]) -> str:
	state = fips <= FIPS_INVALID
	for row in rows:
		if match_region(fips, abbr, state, row):
			if state:
				if abbr == 'GA':
					return "https://en.wikipedia.org/wiki/Georgia_(U.S._state)"
				return "https://en.wikipedia.org/wiki/" + str(us.states.lookup(abbr)).replace(" ", "_")
			elif not row['fips']:
				return "https://en.wikipedia.org/wiki/New_York_City"
			elif row['fips'] == "06075":
				return "https://en.wikipedia.org/wiki/San_Francisco"
			else:
				return "https://en.wikipedia.org/wiki/" + row['county'].replace(" ", "_") + "_County,_" + row['state']
	return ""

# get estimated population from wikipedia
def get_wikipedia_population(fips: int, abbr: str, rows: List[Dict[str, str]]) -> int:
	url = build_wikipedia_url(fips, abbr, rows)
	if not url:
		return -1
	html = ""
	try:
		html = urllib.request.urlopen(url + "_(state)").read().decode("utf-8")
		print(url + "_(state)")
	except:
		html = urllib.request.urlopen(url).read().decode("utf-8")
		print(url)
	match = re.search(r"Estimate.+?(?=\<td\>)\<td\>(\d{1,3}(,\d{3})*)", html)
	best = -1
	if match:
		best = int(match.group(1).replace(",", ""))
	match = re.search(r"Population.+?(?=\<td\>)\<td\>(\d{1,3}(,\d{3})*)", html)
	if match:
		next = int(match.group(1).replace(",", ""))
		if next > best:
			best = next
	return best

def build_lists(fips: int, abbr: str, state: bool, rows: List[Dict[str, str]], days: List[str], counts: List[int], deaths: List[int], \
	ctp_key: str , ctp_key_data: List[int]):
	for row in rows:
		if match_region(fips, abbr, state, row):
			if ctp_key and ctp_key in row:
				try:
					value = int(int(row[ctp_key]))
					ctp_key_data.append(value)
				except:
					continue
					
			days.append(row['date'])
			if abbr and len(counts) > 0 and not state:
				# ww data
				# deltas instead of totals, trim off any time until we get cases
				new_counts = counts[-1] + int(row['cases'])
				if new_counts > 0:
					counts.append(new_counts)
					deaths.append(deaths[-1] + int(row['deaths']))
			else:
				counts.append(int(row['cases']))
				deaths.append(int(row['deaths']))

def get_region(fips: int, abbr: str, state: bool, rows: List[Dict[str, str]]) -> str:
	for row in rows:
		if match_region(fips, abbr, state, row):
			if state:
				return str(us.states.lookup(abbr))
			else:
				county = row['county'].lower().replace(" ", "_")
				state = row['state'].lower().replace(" ", "_")
				return county + "_" + state + "_" + row['fips']
	return ""

# find root of this func
def func_root(x, f, d) -> float:
	"""x = doubling time, func at the doubling time is 2x the base args f(d)"""
	return f(x+d) - 2.0*f(d)

# get roots with days buffer on the end since we're not extrapolating
def get_roots(f, days_deltas, days, roots: List[float]) -> bool:
	roots.clear()
	try:
		compute_days = len(days_deltas)-days
		for x in range(0, compute_days):
			sol = optimize.root_scalar(func_root, args=(f, days_deltas[x]), method="brentq", bracket=[0, days_deltas[-1] - days_deltas[x]])
			roots.append(sol.root)
		return True
	except:
		return False

# performs computation and plots graph line	
def plot(fips: int, abbr: str, state: bool, rows: List[Dict[str, str]], type: PlotType, ctp_key: str):
	if fips <= FIPS_INVALID and not abbr:
		return

	days_data = []
	days_deltas = [0]
	cases_data = []
	deaths_data = []
	ctp_key_data = []

	build_lists(fips, abbr, state, rows, days_data, cases_data, deaths_data, ctp_key, ctp_key_data)
	days_data = days_data[len(days_data)-len(cases_data):]
	
	population = -1
	if 'population' in rows[0]:
		print(abbr)
		for row in rows:
			if match_region(fips, abbr, state, row):
				population = row['population']
				break
	else:
		population = get_wikipedia_population(fips, abbr, rows)
	print(population)

	date_list = [dt.datetime.strptime(x, "%Y-%m-%d") for x in days_data]
	for idx in range(1, len(date_list)):
		delta = date_list[idx] - date_list[0]
		days_deltas.append(delta.days)

	cases = np.asarray(cases_data)
	cases_1000 = np.divide(cases, float(population) / 1000)
	cases_1000_gradient = np.gradient(cases_1000)
	deaths = np.asarray(deaths_data)
	deaths_1000 = np.divide(deaths, float(population) / 1000)
	deaths_1000_gradient = np.gradient(deaths_1000)
	cases_grad = np.gradient(cases)
	deaths_grad = np.gradient(deaths)
	ctp_key_data = np.asarray(ctp_key_data)
	ctp_key_data_1000 = np.divide(ctp_key_data, float(population) / 1000)
	if state and covid_key:
		label = get_region(fips, abbr, state, rows) + "_" + covid_key
		if type == PlotType.COVID_TRACKING_KEY_1000:
			label = label + "_1000"
	else:
		label = get_region(fips, abbr, state, rows) + "_" + type.name.lower()

	roots = []
	
	# doubling time, don't assume a curve fit to get data for the end, instead just truncate and use lerp'd points
	# this means no data for the end of the curve, but also no assumptions about the curve form
	f = interpolate.interp1d(np.asarray(days_deltas), cases)
	days = 1
	while days < len(date_list):
		if get_roots(f, days_deltas, days, roots):
			break;
		else:
			days = days + 1

	if type == PlotType.CASES_DOUBLING:
		date_list = date_list[:len(days_deltas)-days]
	
	switcher = {
		PlotType.CASES: cases,
		PlotType.DEATHS: deaths,
		PlotType.CASES_GRADIENT: cases_grad,
		PlotType.DEATHS_GRADIENT: deaths_grad,
		PlotType.CASES_1000: cases_1000,
		PlotType.DEATHS_1000: deaths_1000,
		PlotType.CASES_DOUBLING: roots,
		PlotType.CASES_1000_GRADIENT: cases_1000_gradient,
		PlotType.DEATHS_1000_GRADIENT: deaths_1000_gradient,
		PlotType.COVID_TRACKING_KEY: ctp_key_data,
		PlotType.COVID_TRACKING_KEY_1000: ctp_key_data_1000
	}
	plt.plot(date_list, switcher.get(type), label=label)

# first arg is fips county code; see https://en.wikipedia.org/wiki/FIPS_county_code
# here we take -1 to be nyc
# if this doesn't work (non-integral), assume it is geo country code or state 
fips = FIPS_INVALID
region_abbr = ""
region_as_state = False

try:
	fips = int(sys.argv[1])
except:
	region_abbr = sys.argv[1]

vs_fips = FIPS_INVALID
vs_region_abbr = ""
vs_region_as_state = False

# parse options
update_data = False
plot_type = PlotType.DEATHS
covid_key = ""
days_out = 6
arg = 2
while arg < len(sys.argv):
	if sys.argv[arg] == "-update":
		update_data = True
		arg = arg + 1
	elif sys.argv[arg] == "-vs":
		try:
			vs_fips = int(sys.argv[arg+1])
		except:
			vs_region_abbr = sys.argv[arg+1]
		arg = arg + 2
	elif sys.argv[arg] == "-type":
		plot_type = PlotType[sys.argv[arg+1].upper()]
		print(plot_type)
		if is_covid_tracking_type(plot_type):
			# covid key types require key with casing
			covid_key = sys.argv[arg+2]
			arg = arg + 3
		else:
			arg = arg + 2
	elif sys.argv[arg] == "-state":
		# interpret first region_abbr as state code for covid tracking instead of country code
		region_as_state = True
		arg = arg + 1
	elif sys.argv[arg] == "-vsstate":
		# interpret vs region_abbr as state code for covid tracking instead of country code
		vs_region_as_state = True
		arg = arg + 1
	else:
		sys.stderr.write("error: unknown arg " + sys.argv[arg])
		sys.exit(-1)

# optional download csv(s)
if update_data:
	download_csv("https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv", get_file_name(), False)
	download_csv("https://opendata.ecdc.europa.eu/covid19/casedistribution/csv", get_file_name_ww(), True)
	download_csv("https://covidtracking.com/api/v1/states/daily.csv", get_file_name_covid_tracking(), False)

# read csv(s)
rows = []
with open(get_file_name(), "r") as csv_file:
	reader = csv.DictReader(csv_file)
	for row in reader:
		rows.append(row)

rows_ww = []
with open(get_file_name_ww(), "r") as csv_file:
	reader = csv.DictReader(csv_file)
	for row in reader:
		# translate to nyt format
		tmp = {}
		tmp['date'] = row['year'] + "-" + row['month'] + "-" + row['day']
		tmp['cases'] = row['cases']
		tmp['deaths'] = row['deaths']
		tmp['county'] = row['countriesAndTerritories']
		tmp['state'] = row['countryterritoryCode']
		tmp['fips'] = ""

		# extras
		tmp['geo'] = row['geoId']
		tmp['population'] = row['popData2018']

		# reverse order
		rows_ww.insert(0, tmp)
		
rows_ctp = []
with open(get_file_name_covid_tracking(), "r") as csv_file:
	reader = csv.DictReader(csv_file)
	for row in reader:
		# translate to nyt format; includes all extras
		tmp = row
		date = row['date']
		tmp['date'] = date[:4] + "-" + date[4:6] + "-" + date[6:8]
		tmp['cases'] = row['positive']
		if row['death']:
			tmp['deaths'] = row['death']
		else:
			row['deaths'] = "0"
		tmp['county'] = ""
		tmp['state'] = row['state']
		tmp['fips'] = ""

		# reverse order
		rows_ctp.insert(0, tmp)
		
# plot
ax = plt.gca()

formatter = dates.DateFormatter("%m-%d")
ax.xaxis.set_major_formatter(formatter)

locator = dates.AutoDateLocator(minticks=3, maxticks=7)
ax.xaxis.set_major_locator(locator)

next_citation = 1
citations = ""
if fips > FIPS_INVALID or vs_fips > FIPS_INVALID:
	citations = str(next_citation) + " - US county data from The New York Times - https://github.com/nytimes/covid-19-data"
	next_citation = next_citation + 1
if region_abbr or vs_region_abbr:
	if region_as_state or vs_region_as_state:
		citations = citations + "\n" + str(next_citation) + " - US state data from https://covidtracking.com"
		next_citation = next_citation + 1
	if (region_abbr and not region_as_state) or (vs_region_abbr and not vs_region_as_state):
		citations = citations + "\n" + str(next_citation) + " - WW data from https://opendata.ecdc.europa.eu/covid19"
		next_citation = next_citation + 1

if needs_wikipedia_citation(fips, region_as_state, plot_type):
	if region_as_state:
		citations = citations + "\n" + str(next_citation) + " - Estimated population - " + build_wikipedia_url(fips, region_abbr, rows_ctp)
	else:
		citations = citations + "\n" + str(next_citation) + " - Estimated population - " + build_wikipedia_url(fips, region_abbr, rows)
	next_citation = next_citation + 1

if region_abbr:
	if region_as_state:
		title = get_region(fips, region_abbr, True, rows_ctp) + "_" + plot_type.name.lower() + "_" + covid_key
	else:
		title = get_region(fips, region_abbr, False, rows_ww) + "_" + plot_type.name.lower()
else:
	title = get_region(fips, region_abbr, False, rows) + "_" + plot_type.name.lower()
	
if vs_fips > FIPS_INVALID or vs_region_abbr:
	if vs_region_abbr:
		if vs_region_as_state:
			title = title + "_vs_" + get_region(vs_fips, vs_region_abbr, True, rows_ctp)
		else:
			title = title + "_vs_" + get_region(vs_fips, vs_region_abbr, False, rows_ww)
	else:
		title = title + "_vs_" + get_region(vs_fips, vs_region_abbr, False, rows)
	if needs_wikipedia_citation(vs_fips, vs_region_as_state, plot_type):
		if vs_region_as_state:
			citations = citations + "\n" + str(next_citation) + " - Estimated population - " + build_wikipedia_url(vs_fips, vs_region_abbr, rows_ctp)
		else:
			citations = citations + "\n" + str(next_citation) + " - Estimated population - " + build_wikipedia_url(vs_fips, vs_region_abbr, rows)

plt.title("\n".join(wrap(title, 60)))
plt.xlabel("Date")
plt.figtext(0.05, 0.0, citations, horizontalalignment="right", fontsize=6, va="top", ha="left")

if region_abbr:
	if region_as_state:
		plot(fips, region_abbr, True, rows_ctp, plot_type, covid_key)
	else:
		plot(fips, region_abbr, False, rows_ww, plot_type, covid_key)
else:
	plot(fips, region_abbr, False, rows, plot_type, covid_key)

if vs_region_abbr:
	if vs_region_as_state:
		plot(vs_fips, vs_region_abbr, True, rows_ctp, plot_type, covid_key)
	else:
		plot(vs_fips, vs_region_abbr, False, rows_ww, plot_type, covid_key)
else:
	plot(vs_fips, vs_region_abbr, False, rows, plot_type, covid_key)

plt.legend()
plt.savefig(title + ".png", bbox_inches="tight")