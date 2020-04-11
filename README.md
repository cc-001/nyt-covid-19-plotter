# nyt-covid-19-plotter
Plots Covid-19 data from The New York Times with USA population data from Wikipedia.

Includes support for world-wide data from:

https://www.ecdc.europa.eu/en/publications-data/download-todays-data-geographic-distribution-covid-19-cases-worldwide

the European Centre for Disease Prevention and Control. See their website for details.  Population data comes from that same download rather than from Wikipedia.

Includes support for Covid-19 Tracking Project data from:

https://covidtracking.com/

population data is not available from them so again it comes from Wikipedia.

**License/Attribution**

Completely free and clear with no citations or links necessary, have at it.

**Install**

This requires a fairly up to date python 3 install along with any required modules.  All the required modules can be installed using pip (pip3).

Ex:

```
pip install scipy numpy matplotlib requests_ntlm us
```

Install whatever you're missing this way.  This was done quickly in a couple hours on the weekend so it's not handling errors or telling you how to use it.

**FIPS Codes**

The county is looked up using the FIPS code, in this case it needs to be the full code with the state:  https://en.wikipedia.org/wiki/FIPS_county_code

New York City is treated as a special case because this data is from The New York Times:  https://github.com/nytimes/covid-19-data  

NYC FIPS code (doesn't exist) is -1 in this tool, otherwise it is the full FIPS code including the state.

**Country Code - "geoId"**

This can be used instead of a FIPS code for world-wide data.  It seems to be a two letter code from https://www.iban.com/country-codes which seems to work.

**State Abbreviation**

If argument:

```
-state
```

is supplied the first arg is treated as a two letter state abbreviation instead of Country Code.

```
-vsstate
```

for vs comparisons where the vs arg should be treated as a two letter state abbreviation.

**Doubling Time**

This is the sexy kid that everyone is talking about.  I didn't assume a curve type like exponential, instead I linearly interpolate the actual data and go as far as I can until it breaks.  The advantage to this is I'm not assuming anything about the curve for extrapolation; the disadvantage is that it's going to lag until the solver can solve it.

**Usage**

```
python plotter.py <fips/geoId> -type(optional) <type> -vs(optional) <fips/geoId> -update(optional)

-update - Downloads and caches data, run this first and whenever you want to update it
-type - one of:  cases, deaths, cases_1000, deaths_1000, cases_gradient, deaths_gradient
-vs - fips code or country code, versus mode draws an additional plot line for comparison
-state - treat non integral code as two letter state abbreviation for Covid-19 Tracking Project
-vsstate - treat non integral code as two letter state abbreviation for Covid-19 Tracking Project

cases - Case count
deaths - Death count
cases_1000 - Cases per-1000 population
deaths_1000 - Deaths per-1000 population
cases_gradient - Derivative (change rate) of cases
deaths_gradient - Derivative (change rate) of deaths
cases_doubling - Doubling time in days
cases_1000_gradient - Derivative (change rate) of cases_1000, useful for vs comparisons
deaths_1000_gradient - Derivative (change rate) of deaths_1000, useful for vs comparisons
covid_tracking_key <key> = Plot this key from Covid-19 Tracking Project, see data covid_tracking_states_daily.csv
covid_tracking_key_1000 <key> = Plot this key from Covid-19 Tracking Project per-1000 population, see data covid_tracking_states_daily.csv
```

**Note**

Covid-19 can only be mixed with other types on cases/deaths and cases_1000/deaths_1000.

**Examples (Win64):**

Covid-19 state by state comparison on key per-1000 population.

```
D:\Temp\v2>python plotter.py CA -state -type COVID_TRACKING_KEY_1000 inIcuCurrently -vs NY -vsstate
https://en.wikipedia.org/wiki/California_(state)
39512223
https://en.wikipedia.org/wiki/New_York_(state)
19453561
```

![Output](https://github.com/cc-001/nyt-covid-19-plotter/blob/master/California_covid_tracking_key_1000_inIcuCurrently_vs_New%20York.png)

Mixing state data from Covid-19 Project and WW data.

```
D:\Temp\v2>python plotter.py CA -state -type DEATHS_1000 -vs US
PlotType.DEATHS_1000
https://en.wikipedia.org/wiki/California_(state)
39512223
US
327167434
```
![Output](https://github.com/cc-001/nyt-covid-19-plotter/blob/master/California_deaths_1000__vs_united_states_of_america_usa_.png)

```
D:\Temp\v2>python plotter.py 06075 -vs 06081 -type cases_1000
https://en.wikipedia.org/wiki/San_Francisco
https://en.wikipedia.org/wiki/San_Francisco
883305
https://en.wikipedia.org/wiki/San_Mateo_County,_California
https://en.wikipedia.org/wiki/San_Mateo_County,_California
769545
```
![Output](https://github.com/cc-001/nyt-covid-19-plotter/blob/master/san_francisco_california_06075_cases_1000_vs_san_mateo_california_06081.png)

```
D:\Temp\v2>python plotter.py 06075 -vs 06081 -type cases_gradient
https://en.wikipedia.org/wiki/San_Francisco
https://en.wikipedia.org/wiki/San_Francisco
883305
https://en.wikipedia.org/wiki/San_Mateo_County,_California
https://en.wikipedia.org/wiki/San_Mateo_County,_California
769545
```
![Output](https://github.com/cc-001/nyt-covid-19-plotter/blob/master/san_francisco_california_06075_cases_gradient_vs_san_mateo_california_06081.png)

```
D:\Temp\v2>python plotter.py 06081 -type cases_doubling
https://en.wikipedia.org/wiki/San_Mateo_County,_California
https://en.wikipedia.org/wiki/San_Mateo_County,_California
769545
```

![Output](https://github.com/cc-001/nyt-covid-19-plotter/blob/master/san_mateo_california_06081_cases_doubling.png)

```
D:\Temp\v2>python plotter.py -1 -type deaths_1000_gradient -vs 22071
https://en.wikipedia.org/wiki/New_York_City
https://en.wikipedia.org/wiki/New_York_City
8398748
https://en.wikipedia.org/wiki/Orleans_County,_Louisiana
https://en.wikipedia.org/wiki/Orleans_County,_Louisiana
391006
```

![Output](https://github.com/cc-001/nyt-covid-19-plotter/blob/master/new_york_city_new_york__deaths_1000_gradient_vs_orleans_louisiana_22071.png)

```
D:\Temp\v2>python plotter.py CZ -type cases_1000 -vs -1
CZ
10625695
https://en.wikipedia.org/wiki/New_York_City
8398748
```
![Output](https://github.com/cc-001/nyt-covid-19-plotter/blob/master/czech_republic_cze__cases_1000_vs_new_york_city_new_york_.png)
