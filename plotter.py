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

def get_path() -> str:
	return os.path.join(os.getcwd(), "Data")

def get_file_name() -> str:
	return os.path.join(get_path(), "us-counties.csv")

def match_fips(fips: int, row: Dict[str, str]) -> bool:
	if not row['fips']:
		return row['county'] == "New York City" and fips == -1
	return int(row['fips']) == fips

def build_wikipedia_url(fips: int, rows: List[Dict[str, str]]) -> str:
	for row in rows:
		if match_fips(fips, row):
			if not row['fips']:
				return "https://en.wikipedia.org/wiki/New_York_City"
			elif row['fips'] == "06075":
				return "https://en.wikipedia.org/wiki/San_Francisco"
			else:
				return "https://en.wikipedia.org/wiki/" + row['county'].replace(" ", "_") + "_County,_" + row['state']
	return ""

# get estimated population from wikipedia
def get_wikipedia_population(fips: int, rows: List[Dict[str, str]]) -> int:
	url = build_wikipedia_url(fips, rows)
	print(url)
	if not url:
		return -1
	html = urllib.request.urlopen(url).read().decode("utf-8")
	match = re.search(r"Estimate.+?(?=\<td\>)\<td\>(\d{1,3}(,\d{3})*)", html)
	if match:
		return int(match.group(1).replace(",", ""))
	match = re.search(r"Population.+?(?=\<td\>)\<td\>(\d{1,3}(,\d{3})*)", html)
	if match:
		return int(match.group(1).replace(",", ""))
	return -1

def build_lists(fips: int, rows: List[Dict[str, str]], days: List[str], counts: List[int], deaths: List[int]):
	for row in rows:
		if match_fips(fips, row):
			days.append(row['date'])
			counts.append(int(row['cases']))
			deaths.append(int(row['deaths']))

def get_county_state(fips: int, rows: List[Dict[str, str]]) -> str:
	for row in rows:
		if match_fips(fips, row):
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
def plot(fips: int, rows: List[Dict[str, str]], type: PlotType):
	if fips < -1:
		return

	days_data = []
	days_deltas = [0]
	cases_data = []
	deaths_data = []

	build_lists(fips, rows, days_data, cases_data, deaths_data)
	population = get_wikipedia_population(fips, rows)

	date_list = [dt.datetime.strptime(x, "%Y-%m-%d") for x in days_data]
	for idx in range(1, len(date_list)):
		delta = date_list[idx] - date_list[0]
		days_deltas.append(delta.days)
		
	population = get_wikipedia_population(fips, rows)
	print(population)

	cases = np.asarray(cases_data)
	cases_1000 = np.divide(cases, float(population) / 1000)
	cases_1000_gradient = np.gradient(cases_1000)
	deaths = np.asarray(deaths_data)
	deaths_1000 = np.divide(deaths, float(population) / 1000)
	deaths_1000_gradient = np.gradient(deaths_1000)
	cases_grad = np.gradient(cases)
	deaths_grad = np.gradient(deaths)
	label = get_county_state(fips, rows) + "_" + type.name.lower()

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
		PlotType.DEATHS_1000_GRADIENT: deaths_1000_gradient
	}
	plt.plot(date_list, switcher.get(type), label=label)

# first arg is fips county code; see https://en.wikipedia.org/wiki/FIPS_county_code
# here we take -1 to be nyc
fips = int(sys.argv[1])
vs_fips = -2

# parse options
update_data = False
plot_type = PlotType.DEATHS
days_out = 6
arg = 2
while arg < len(sys.argv):
	if sys.argv[arg] == "-update":
		update_data = True
		arg = arg + 1
	elif sys.argv[arg] == "-vs":
		vs_fips = int(sys.argv[arg+1])
		arg = arg + 2
	elif sys.argv[arg] == "-type":
		plot_type = PlotType[sys.argv[arg+1].upper()]
		arg = arg + 2
	else:
		sys.stderr.write("error: unknown arg " + sys.argv[arg])
		sys.exit(-1)

# optional download csv from github
if update_data:
	url = "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv"
	html = urllib.request.urlopen(url).read().decode("utf-8")
	path = get_path()
	if not os.path.exists(path):
		os.mkdir(path)
	file = open(get_file_name(), "w")
	file.write(html)
	file.close()

# read csv
rows = []
with open(get_file_name(), "r") as csv_file:
	reader = csv.DictReader(csv_file)
	for row in reader:
		rows.append(row)			

# plot
ax = plt.gca()

formatter = dates.DateFormatter("%m-%d")
ax.xaxis.set_major_formatter(formatter)

locator = dates.AutoDateLocator(minticks=3, maxticks=7)
ax.xaxis.set_major_locator(locator)

citations = "1 - Data from The New York Times - https://github.com/nytimes/covid-19-data"
next_citation = 2
if plot_type == PlotType.CASES_1000 or plot_type == PlotType.DEATHS_1000:
	citations = citations + "\n" + str(next_citation) + " - Estimated population - " + build_wikipedia_url(fips, rows)
	next_citation = next_citation + 1

title = get_county_state(fips, rows) + "_" + plot_type.name.lower()
if vs_fips >= -1:
	title = title + "_vs_" + get_county_state(vs_fips, rows)
	if plot_type == PlotType.CASES_1000 or plot_type == PlotType.DEATHS_1000:
		citations = citations + "\n" + str(next_citation) + " - Estimated population - " + build_wikipedia_url(vs_fips, rows)

plt.title("\n".join(wrap(title, 60)))
plt.xlabel("Date")
plt.figtext(0.05, 0.0, citations, horizontalalignment="right", fontsize=6, va="top", ha="left")

plot(fips, rows, plot_type)
plot(vs_fips, rows, plot_type)

plt.legend()
plt.savefig(title + ".png", bbox_inches="tight")