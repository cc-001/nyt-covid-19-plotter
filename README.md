# nyt-covid-19-plotter
Plots Covid-19 data from The New York Times with population data from Wikipedia.

**License/Attribution**

Completely free and clear with no citations or links necessary, have at it.

**Install**

This requires a fairly up to date python 3 install along with any required modules.  All the required modules can be installed using pip (pip3).

Ex:

```
pip install numpy
```

Install whatever you're missing this way.  This was done quickly in a couple hours on the weekend so it's not handling errors or telling you how to use it.

**FIPS Codes**

The county is looked up using the FIPS code, in this case it needs to be the full code with the state:  https://en.wikipedia.org/wiki/FIPS_county_code

New York City is treated as a special case because this data is from The New York Times:  https://github.com/nytimes/covid-19-data  

NYC FIPS code (doesn't exist) is -1 in this tool, otherwise it is the full FIPS code including the state.

**Doubling Time**

This is the sexy kid that everyone is talking about.  I didn't assume a curve type like exponential, instead I linearly interpolate the actual data and go as far as I can until it breaks.  The advantage to this is I'm not assuming anything about the curve for extrapolation; the disadvantage is that it's going to lag until the solver can solve it.

**Usage**

```
python plotter.py <fips> -type(optional) <type> -vs(optional) <fips> -update(optional)

-update - Downloads and caches data from github, run this first and whenever you want to update it
-type - one of:  cases, deaths, cases_1000, deaths_1000, cases_gradient, deaths_gradient
-vs - fips code, versus mode draws an additional plot line for comparison

cases - Case count
deaths - Death count
cases_1000 - Cases per-1000 population from Wikipedia estimated value
deaths_1000 - Deaths per-1000 population from Wikipedia estimated value
cases_gradient - Derivitive (change rate) of cases
deaths_gradient - Derivitive (change rate) of deaths
cases_doubling - Doubling time in days
```

Ex (Win64):

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
