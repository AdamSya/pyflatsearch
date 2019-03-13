# pyflatsearch
A data mining and visualisation tool for obtaining current information on property prices in different wards of London
The script uses package <code>rightmove_webscraper</code> to mine the data from www.rightmove.co.uk and <code>geopandas</code> and <code>matplotlib</code> packages to plot the data on a map.

## Installation

`pyflatsearch` can only be run on a machine running Python 3 which can be downloaded here: https://www.python.org/downloads/

The following packages are also required for  `pyflatsearch` to work:

`shapely` `geopandas` `pandas` `rightmove_webscraper` `seaborn` `numpy` `matplotlib`

To install the packages, please type: `pip3 install <package name>` 

## How to use
1.  Run <code>pyflatsearch.py</code> in your terminal.
    ![image-20190313000242524](/Users/adamsyanda/Library/Application Support/typora-user-images/image-20190313000242524.png)
2.  Type in location for the search. Currently, `London` is the only search location. Press **Enter** to continue to next prompts (*Default value:* `London`).![image-20190313000528085](/Users/adamsyanda/Library/Application Support/typora-user-images/image-20190313000528085.png)
3.  Type in the minimum property monthly rental price as an integer. For example, for £500pcm type in `500`. *(Default value:* `0`).![image-20190313000630581](/Users/adamsyanda/Library/Application Support/typora-user-images/image-20190313000630581.png)
4.  Type in the maximum property monthly rental price as an integer. For example, for £1500pcm type in `1500`. (*Default value:* `400`).![image-20190313000751953](/Users/adamsyanda/Library/Application Support/typora-user-images/image-20190313000751953.png)
5.  Type in the search radius in miles. For example, for a 5 mile radius type in `5`. (*Default value:* `0`)![image-20190313001450245](/Users/adamsyanda/Library/Application Support/typora-user-images/image-20190313001450245.png)
6.  Type in the property type from the following options: `house` `flat` `bungalow` `land` `park home` `student halls` (*Default value:* `flat`).![image-20190313001757523](/Users/adamsyanda/Library/Application Support/typora-user-images/image-20190313001757523.png)
7.  Type in the minimum bedroom number as an integer. For example, for a studio flat type in `0`, and for a 3-bedroom property type in `3` (*Default value:* `1`).![image-20190313002114266](/Users/adamsyanda/Library/Application Support/typora-user-images/image-20190313002114266.png)
8.  Type in the maximum bedroom number as an integer. For example, for a 1-bedroom property type in `1`, and for a 3-bedroom property type in `3`. If the minimum and maximum number is equal, pyflatsearch will only search properties with the chosen number of bedrooms (*Default value:* `1`).![image-20190313002323017](/Users/adamsyanda/Library/Application Support/typora-user-images/image-20190313002323017.png)
9.  Choose whether to search exclusively furnished (type in `furnished`), part-furnished (type in `part`) or unfurnished (type in `unfurnished`) properties. If no value is passed, the search results will include all properties irrespectively of the furniture status. (*Default value:* `None`). ![image-20190313002629554](/Users/adamsyanda/Library/Application Support/typora-user-images/image-20190313002629554.png)
10.  Choose whether to seach exclusively for long-term (type in `longterm`), short-term (type in `shortterm`) or student properties (type in `student`). If no value is passed, the search results will include all properties irrespectively of the tenancy length (*Default value:* `None`).  ![image-20190313002842297](/Users/adamsyanda/Library/Application Support/typora-user-images/image-20190313002842297.png)
11.  Choose whether to include properties that have been put on hold due to a new tenant submitting their deposit. To include such properties type in `y` and to exclude type in `n` (*Default value:* `true`).![image-20190313003057226](/Users/adamsyanda/Library/Application Support/typora-user-images/image-20190313003057226.png)
12.  The initial output displays the link for the search. Below you can also see the sample size (1050 properties) and how it compares to all properties that fullfil the search criteria (12%). Due to the way Rightmove.co.uk is designed, the upper limit for the search is 1050 properties. The estimated completion time was established by timing the tool on the local machine so the values might not be very accurate.![image-20190313003619025](/Users/adamsyanda/Library/Application Support/typora-user-images/image-20190313003619025.png)
13.  The search data is saved as csv files in the **output** folder. The full results file contains the following columns: `index` (index in the postcode data set), `price` (rental price) ,`address` (address), `postcode` (postcode), `ward` (ward), `district` (district), `distance` (distance from the nearest station), `lat` (latitude), `long` (longitude). The summary results file contains the following columns: `ward` (ward), `price` (mean property price in the ward).![image-20190313004450752](/Users/adamsyanda/Library/Application Support/typora-user-images/image-20190313004450752.png)
14.  The visual output includes files in two formats: **jpeg** and **pdf** at 200dpi. The map shows a kernel density plot with a colorbar to demonstrate pricing in different wards of London. Below, a scatterplot shows the mean (white circle) and range of values (coloured bar) in districts with most results (each property is a colored circle; up to 15 districts shown). The size of the colored circle reflects the distance from the nearest station and can be compared with the grey circles in the legend.
     ![image-20190313010110749](/Users/adamsyanda/Library/Application Support/typora-user-images/image-20190313010110749.png)
     ![image-20190313010442411](/Users/adamsyanda/Library/Application Support/typora-user-images/image-20190313010442411.png)

## Future updates

- Create a one-command line interface for the program.
- Improve the coding structure and conform with GitHub/Python package standards.
- Add the package to PyPi.
- Add more cities.
- Combine the collected data in a day to track changes in rental property prices over time.
- **Eventually:** Create an interactive version of the charts in Dash.