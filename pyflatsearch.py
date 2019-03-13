import re
import urllib.request
import numpy as np
from shapely.ops import cascaded_union
import geopandas as gpd
import pandas as pd
pd.set_option('display.expand_frame_repr', False)
from rightmove_webscraper import rightmove_data
from time import sleep
from datetime import datetime
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from descartes import PolygonPatch
from matplotlib.lines import Line2D
import warnings
warnings.filterwarnings('ignore')

def user_input():
    """Attributes to search on Rightmove"""
    #   default dictionary for the results
    inputdict = {'city':'REGION%5E87490',
                 'minprice':0,
                 'maxprice':400,
                 'radius':0,
                 'propertytype':'flat',
                 'min_number_bedrooms':1,
                 'max_number_bedrooms':1,
                 'furnishTypes':'',
                 'letType':'',
                 'includeLetAgreed':'true'}

    try:
        city = input('Location: ')
        cities = {'London': 'REGION%5E87490'}
        inputdict['city'] = cities[city]
    except:
        print('Incorrect input. Using the default value of: London')
        pass

    try:
        min_price = input('Property lower price limit in British Pounds (integer): ')
        inputdict['minprice'] = int(min_price)
    except:
        print('Incorrect input. Using the default value of: %d' % inputdict['minprice'])
        pass

    try:
        max_price = int(input('Property upper price limit in British Pounds (integer): '))
        inputdict['maxprice'] = int(max_price)
    except:
        print('Incorrect input. Using the default value of: %d' % inputdict['maxprice'])
        pass

    try:
        radius = input('Search area radius (mi; integer): ')
        inputdict['radius'] = int(radius)
    except:
        print('Incorrect input. Using the default value of: %d' % inputdict['radius'])

    try:
        proptype_dict = {'house': 'Houses', 'flat': 'flat', 'bungalow': 'bungalow', 'land': 'land',
                         'park home': 'park-home', 'student halls': 'private-halls'}
        proptype = input('Property type ' + str([i for i in proptype_dict]) + ': ').lower()
        if proptype in proptype_dict:
            inputdict['propertytype'] = proptype_dict[proptype]
    except:
        print('Incorrect input. Using the default value of: %d' % inputdict['propertytype'])
        pass

    try:
        min_number_bedrooms = input('Please enter minimum bedroom number (integer): ')
        inputdict['min_number_bedrooms'] = int(min_number_bedrooms)
    except:
        print('Incorrect input. Using the default value of: %d' % inputdict['min_number_bedrooms'])
        pass

    try:
        max_number_bedrooms = input('Please enter maximum bedroom number (integer): ')
        inputdict['max_number_bedrooms'] = int(max_number_bedrooms)
    except:
        print('Incorrect input. Using the default value of: %d' % inputdict['max_number_bedrooms'])
        pass

    try:
        furndict = {'furnished':'furnished',
                    'part':'partFurnished',
                    'unfurnished':'unfurnished'}
        furnished = input("Furnished type ['furnished','part','unfurnished']: ")
        if furnished in furndict:
            inputdict['furnishTypes'] = furndict[furnished]
    except:
        print('Incorrect input. Using the default value of: %d' % inputdict['furnishTypes'])
        pass

    try:
        lettypedict = {'longterm':'longTerm',
                       'shortterm':'shortTerm',
                       'student':'student'}
        lettype = input("Please enter the type of let ['longterm','shortterm','student']: ")
        if lettype in lettypedict:
            inputdict['letType'] = lettypedict[lettype]
    except:
        print('Incorrect input. Using the default value of: %d' % inputdict['letType'])
        pass

    try:
        incl_letdict = {'y':'true',
                        'n':'false'}
        incl_let = input("Include let agreed properties - properties currently on hold ['Y','N']: ").lower()
        if incl_let in incl_letdict:
            inputdict['includeLetAgreed'] = incl_letdict[incl_let]
    except:
        print('Incorrect input. Using the default value of: %d' % inputdict['includeLetAgreed'])
        pass
    return inputdict

def load_local_data(map_file, postcode_file):
    """Loader for local data i.e. shp map file and the list of postcodes"""

    # Load the map of London in shp and shx format (both required)
    map_df = gpd.read_file(map_file)
    print('Loaded the map of London: '+map_file)

    # Load a list of London postcodes and extract relevant columns
    postcode_data = pd.read_csv(postcode_file)
    post_extracted_data = postcode_data[['Postcode','Ward','District','Distance to station','Latitude','Longitude']].reset_index()
    print('Loaded London postcodes: ' + str(postcode_file))

    return map_df,post_extracted_data

def rightmove_scraper():
    """The function uses package rightmove_webscraper to mine data from RightMove.co.uk
    "   Author: woblers
    "   github: https://github.com/woblers/rightmove_webscraper.py
    """
    #   Load the properties using rightmove_webscraper package
    #   Limit of 1050 properties imposed by the website design

    url = 'https://www.rightmove.co.uk/property-to-rent/find.html?' \
            'locationIdentifier=%s&' % inputdict['city']+ \
            'minPrice=%d&' % inputdict['minprice']+ \
            'maxPrice=%d&' % inputdict['maxprice']+ \
            'radius=%.1f&' % inputdict['radius']+ \
            'propertyTypes=%s&' % inputdict['propertytype']+ \
            'minBedrooms=%d&' % inputdict['min_number_bedrooms']+\
            'maxBedrooms=%d&' % inputdict['max_number_bedrooms']+ \
            'furnishTypes=%s&' % inputdict['furnishTypes']+ \
            'letType=%s&' % inputdict['letType'] +\
            'includeLetAgreed=%s' % inputdict['includeLetAgreed'] \

    print('Loading the current property data from Rightmove: '+str(url))
    try:
        rightmove_object = rightmove_data(url)
    except ValueError as ve:
        print('No results found! Try to broaden your search criteria!')
        exit()

    rm_scraper_data = rightmove_object.get_results
    if len(rm_scraper_data.index) >= 1050:
        print('Property data loaded (%d properties). Sample size limit of 1050 has been reached.' % len(rm_scraper_data.index))
    else:
        print('Property data loaded (%d properties).' % len(rm_scraper_data.index))

    #   experimentally derived line of best fit for the completion time based on number of results (n>10)
    e = (len(rm_scraper_data.index)+29)/2.34
    print('Estimated total processing time: %d min %d sec.' % (int(str(e/60)[0]),int(e%60)))

    #   obtaining the total number of properties that fullfill the search criteria reported on the website
    print('Obtaining the reported number of results... ',end='\t')
    op = urllib.request.urlopen(url)
    read_url = op.read()
    sleep(1)
    try:
        no_of_all_results = int(re.findall('resultCount.*?>(\d.*?)<', str(read_url))[0].replace(',',''))
        print(str(no_of_all_results) + ' properties reported on Rightmove (' + "{0:.0f}".format(100*(len(rm_scraper_data.index)/no_of_all_results)) + '% sampled).')
    except:
        print('Number of actual results could not be obtained!')
        no_of_all_results = np.nan

    return rm_scraper_data, no_of_all_results

def postcode_search():
    """Search rightmove HTML page sources for post codes"""
    #   Throttled by 100ms between each query to reduce the impact on Rightmove servers.
    print('Retrieving property postcodes... Please wait...')
    retrieved_postcodes = []
    for url in rm['url']:
        op = urllib.request.urlopen(url)
        read_url = op.read()
        try:
            retrieved_postcodes.append(re.findall('"postcode":"(.*?)"', str(read_url))[0])
        except:
            retrieved_postcodes.append(np.nan)
        sleep(0.1)
    print('%d property postcodes retrieved.' % len(retrieved_postcodes))
    return retrieved_postcodes

def result_analyser():
    """Formats the dataframe to remove unnecessary data"""
    print('Formatting data... ', end='\t')
    #   remove unnecessary column (including an outcode postcode) from the rightmove_webscraper dataset
    rmfiltered = rm.drop(['type','agent_url','search_date','url','postcode','number_bedrooms'], axis=1)
    #   add a column containing the retrieved full postcodes
    rmfiltered['postcode'] = retrieved_postcodes
    #   drop properties lacking crucial info
    curated_properties = rmfiltered.dropna()
    #   match postcodes to obtain ward
    curated_data = curated_properties.merge(post_extracted_data, left_on='postcode', right_on='Postcode')
    curated_data = curated_data.drop(['Postcode'], axis=1)
    curated_data.index = curated_data['index']
    curated_data = curated_data.drop(['index'],axis=1)
    curated_data.columns = ['price', 'address', 'postcode', 'ward', 'district',
       'distance', 'lat', 'long']

    #   obtain average prices per ward in London in a dataframe format
    avg_ward_prices = curated_data[['district','ward','price']].groupby('ward').mean()
    #   obtain average prices per district in London in a dataframe format
    avg_district_prices = curated_data[['district','ward','price']].groupby('district').mean()

    #   get a list of districts with highest number of properties
    highest_dist = curated_data[['district','ward','price']].groupby('district').count().sort_values(by='ward',ascending=False)
    highest_dist = highest_dist.index[:(min(len(highest_dist),15))].tolist()

    #   match wards to get postcode data for the results
    mapped_wards = map_df.merge(avg_ward_prices,left_on='NAME', right_on='ward')
    mapped_wards = mapped_wards.drop(['GSS_CODE','LAGSSCODE','HECTARES','NONLD_AREA'], axis=1)
    print('Data formatted. Curated data has been obtained.')
    return map_df,mapped_wards, avg_ward_prices, avg_district_prices, curated_data,highest_dist

def datasaver():
    """Saves the data as csv"""
    print('Saving data... ',end='')
    outputs = ['output/' +str(datetime.now())[:10] +'_' + str(inputdict['minprice']) +'_' + str(inputdict['maxprice']) + '_' + str(inputdict['min_number_bedrooms']) + '_' + str(inputdict['max_number_bedrooms']) + '_' + str(inputdict['propertytype']) + '_summary.csv',
               'output/' + str(datetime.now())[:10] +'_' + str(inputdict['minprice']) + '_' + str(inputdict['maxprice']) + '_' + str(inputdict['min_number_bedrooms']) + '_' + str(inputdict['max_number_bedrooms']) + '_' + str(inputdict['propertytype']) + '_full.csv']
    #   saves a summary report with ward average prices
    avg_ward_prices.to_csv(outputs[0])
    curated_data.to_csv(outputs[1])
    print('All data saved to the following files:')
    for location in outputs:
        print('\t'+location)

def map_plotter():
    """Plot cholopleth map and scatterplot below it"""
    print('Plotting the map... ', end='')
    fig, ax = plt.subplots(2,1, figsize=(10.7, 8.3),gridspec_kw={'height_ratios':[2, 1]})
    fig.tight_layout(pad=1, w_pad=0.5, h_pad=0.5)
    fig.patch.set_facecolor('#f2f2f2')

    #   set colormap
    cmap = plt.cm.Reds
    cmap.set_under(color='white')

    #   set min and max for the axes, adjust to create some space for legend etc.
    vmin = min(avg_ward_prices['price'])
    vmax = max(avg_ward_prices['price'])
    xmin = lambda x: round(vmin, -2) - 100 if round(vmin, -2) > vmin else round(vmin, -2)-50
    xmax = lambda x: round(vmax, -2) + 100 if round(vmax, -2) <= vmax else round(vmax, -2)+50
    xmin = xmin(xmin)
    xmax = xmax(vmax)

    #   set limits on map axis (coordinates)
    ax[0].set_xlim([500000, 563000])
    ax[0].set_ylim([155000, 202000])
    #   remove axes
    ax[0].axis('off')

    #   use the ward results and obtain the centre of polygon for each ward
    map_pos_wards = mapped_wards[['DISTRICT', 'geometry', 'price']]
    map_pos_wards = map_pos_wards[map_pos_wards['price'] != 0]
    centrx = map_pos_wards['geometry'].apply(lambda c: c.centroid.x)
    centry = map_pos_wards['geometry'].apply(lambda c: c.centroid.y)

    #   set up a kernel density estimation plot masked by the ward boundaries
    j_map = cascaded_union(map_pos_wards['geometry'])
    j = ax[0].add_patch(PolygonPatch(j_map, fc='none', ec='#c1c1c1'))
    try:
        sns.kdeplot(centrx, centry, ax=ax[0], n_levels=len(map_pos_wards.index), cmap=cmap, shade=True, shade_lowest=False,
                    zorder=11, kernel='biw', gridsize=1000, alpha=1)
        for col in ax[0].collections:
            col.set_clip_path(j)
            #   plot map
        map_df.plot(linewidth=0.5, ax=ax[0], edgecolor='#c1c1c1', color='white')
        map_pos_wards.plot(linewidth=0, ax=ax[0], edgecolor='#c1c1c1', column=map_pos_wards['price'], vmin=xmin,
                           vmax=xmax, cmap=cmap, zorder=10)
        ax[0].add_patch(PolygonPatch(j_map, fc='none', ec='#c1c1c1'))
    except ValueError:
        print('Single result cannot be plotted on a kdeplot. Please broaden the search criteria.')
        ax[0].annotate('*', xy=(centrx[0], centry[0]), xycoords='data', horizontalalignment='left',
            verticalalignment='top', fontsize=8, color='black', zorder=11)
        ax[0].annotate('* Single result cannot be plotted on a kernel density estimation plot. Please broaden the search criteria.', xy=(0.25, 0.92), xycoords='figure fraction', horizontalalignment='left',
                       verticalalignment='top',
                       fontsize=8, color='#555555')
        map_df.plot(linewidth=0.5, ax=ax[0], edgecolor='#c1c1c1', color='white')
        map_pos_wards.plot(linewidth=0.8, ax=ax[0], edgecolor='#c1c1c1', column=map_pos_wards['price'], vmin=xmin,
                           vmax=xmax, cmap=cmap, zorder=10)
        ax[0].add_patch(PolygonPatch(j_map, color='gray', ec='#c1c1c1'))

    #   set up the colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=xmin, vmax=xmax))
    sm._A = []
    fig.colorbar(sm,format='£%.0f',ax=ax[0])
    print('Map plotted.\nCreating a scatter plot...', end='')

    #   scatterplot - sorted by average district price
    sns.set(style="whitegrid")
    selected_properties = curated_data[curated_data.district.isin(highest_dist)].sort_values(by='district')
    avg_d_for_sorting = selected_properties[['district','price']].groupby('district').mean()
    avg_d_for_sorting.columns = ['avgprice']
    selected_properties = pd.merge(selected_properties,avg_d_for_sorting,left_on='district',right_on=avg_d_for_sorting.index).sort_values(by='avgprice')

    #   created a simple formula for the marker size
    plot_markersize = [abs(int(-40*a+120)) for a in selected_properties['distance']]
    sns.scatterplot(x="price", y="district", hue='district',
                  data=selected_properties,
                  alpha=0.6, edgecolor='none',zorder=4, s=plot_markersize)


    # adding range bars to the scatterplot (min and max) - it's actually two overlapping bars, one white one colored
    barplotdata = selected_properties[['district','price']]
    bpdata = [[barplotdata[barplotdata['district']==row['district']].min().values[1] for index,row in barplotdata.iterrows()],
              [barplotdata[barplotdata['district'] == row['district']].max().values[1] for index, row in
               barplotdata.iterrows()]]
    barplotdata.loc[:,'min'] = bpdata[0]
    barplotdata.loc[:,'max'] = bpdata[1]

    #   calculating the averages and ensuring each district has only 1 result (to prevent multiple circles on top of each other
    average_circles = [(row['district'], barplotdata[barplotdata['district'] == row['district']].mean().values[0]) for index, row in
               barplotdata.iterrows()]
    avgC = []
    for i in range(len(average_circles)):
        try:
            if average_circles[i][0] == average_circles[i+1][0]:
                avgC.append(np.nan)
            else:
                avgC.append(int(average_circles[i][1]))

        except:
            if i+1 == len(average_circles):
                avgC.append(int(average_circles[i][1]))
            else:
                avgC.append(np.nan)
            pass
    barplotdata.loc[:,'avg'] = avgC

    #   legend for the scatterplot
    legend1 = Line2D(range(1), range(1), linewidth=0, marker='o', markerfacecolor='gray',
                     markeredgewidth=0, markersize=min(plot_markersize) ** (1 / 2.0), alpha=0.6)
    legend2 = Line2D(range(1), range(1), linewidth=0, marker='o', markerfacecolor='gray',
                     markeredgewidth=0, markersize=max(plot_markersize) ** (1 / 2.0), alpha=0.6)
    legend3 = Line2D(range(1), range(1), linewidth=0, marker='o', markersize=5, markerfacecolor="white", fillstyle=None,
                     markeredgecolor='gray', markeredgewidth=0.5, alpha=0.5)
    legend4 = Line2D(range(1), range(1), color="#c6e2ff", linewidth=5, alpha=0.5)
    ax[1].legend((legend1, legend2, legend3, legend4), (
    "{0:.1f} miles\nfrom station".format(max(selected_properties['distance'])),
    "{0:.1f} miles\nfrom station".format(min(selected_properties['distance'])), 'District mean', 'Range'), numpoints=1,
                 loc=1, fontsize=8)

    # actual barplots and scatterplot
    sns.barplot(x='max', y=barplotdata['district'], data=barplotdata,
                 label="Total", alpha=0.5,ci=None,zorder=2)
    sns.barplot(x='min', y=barplotdata['district'], data=barplotdata,
                label="Total", color="white",zorder=3)

    sns.scatterplot(size=5, x=barplotdata['avg'], y=barplotdata['district'], legend=False,
                  data=barplotdata, markers="o", color='white', edgecolor='black',alpha=0.5, zorder=5)  # sns.color_palette("hls", len(new_bar.index)) #sns.hls_palette(8, l=.3, s=.8))             data=new_bar, join=False, markers="s", palette=['black'],zorder=5, alpha=0.5) #sns.color_palette("hls", len(new_bar.index)) #sns.hls_palette(8, l=.3, s=.8))

    print('Scatter plot created. \nAdjusting axes and adding annotations...')

    ax[1].set_xlabel('Price', fontsize=10, color='#555555', fontweight='bold')
    ax[1].set_ylabel('District', fontsize=10, color='#555555', fontweight='bold')
    ax[1].set_xlim([xmin, xmax])

    plt.xticks(fontsize=8, rotation=90)
    ax[1].xaxis.set_major_formatter(FormatStrFormatter('£%.0f'))
    ax[1].xaxis.grid(False)

    plt.yticks(fontsize=8)

    # ANNOTATIONS
    #   add a title...
    ax[0].set_title('Rental property pricing in London on %s\n' % str(datetime.now())[:10], fontsize=16,
                    fontweight='bold', color='#333333')

    # create an annotations for the logo description, and query details
    ax[0].annotate('Powered by:', xy=(0.022, 0.975), xycoords='figure fraction', horizontalalignment='left',
                   verticalalignment='top',
                   fontsize=8, color='#555555')
    fig.figimage(plt.imread('data/rm_logo.png'), xo=50, yo=1520)

    ax[0].annotate('Search query details', xy=(0.022, 0.90), xycoords='figure fraction', horizontalalignment='left',
                   verticalalignment='top', fontsize=8, color='#555555', fontweight='bold')
    ax[0].annotate('Price range:', xy=(0.022, 0.88), xycoords='figure fraction', horizontalalignment='left',
                   verticalalignment='top', fontsize=8, color='#555555')
    ax[0].annotate('£0 - %i' % inputdict['maxprice'], xy=(0.17, 0.88), xycoords='figure fraction',
                   horizontalalignment='left',
                   verticalalignment='top', fontsize=8, color='#555555')
    ax[0].annotate('Search radius:', xy=(0.022, 0.86), xycoords='figure fraction', horizontalalignment='left',
                   verticalalignment='top', fontsize=8, color='#555555')
    ax[0].annotate(str(inputdict['radius']), xy=(0.17, 0.86), xycoords='figure fraction', horizontalalignment='left',
                   verticalalignment='top', fontsize=8, color='#555555')
    ax[0].annotate('Property type:', xy=(0.022, 0.84), xycoords='figure fraction', horizontalalignment='left',
                   verticalalignment='top', fontsize=8, color='#555555')
    ax[0].annotate(inputdict['propertytype'], xy=(0.17, 0.84), xycoords='figure fraction', horizontalalignment='left',
                   verticalalignment='top', fontsize=8, color='#555555')
    ax[0].annotate('No. of bedrooms:', xy=(0.022, 0.82), xycoords='figure fraction', horizontalalignment='left',
                   verticalalignment='top', fontsize=8, color='#555555')
    ax[0].annotate(str(inputdict['min_number_bedrooms'])+' - '+str(inputdict['max_number_bedrooms']), xy=(0.17, 0.82), xycoords='figure fraction', horizontalalignment='left',
                   verticalalignment='top', fontsize=8, color='#555555')
    if len(inputdict['furnishTypes'])>0:
        ax[0].annotate('Furnished:', xy=(0.022, 0.80), xycoords='figure fraction', horizontalalignment='left',
                       verticalalignment='top', fontsize=8, color='#555555')
        ax[0].annotate(str(inputdict['furnishTypes']), xy=(0.17, 0.80), xycoords='figure fraction', horizontalalignment='left',
                       verticalalignment='top', fontsize=8, color='#555555')
    if len(inputdict['letType'])>0:
        ax[0].annotate('Let type:', xy=(0.022, 0.78), xycoords='figure fraction', horizontalalignment='left',
                       verticalalignment='top', fontsize=8, color='#555555')
        ax[0].annotate(str(inputdict['letType']), xy=(0.17, 0.78), xycoords='figure fraction', horizontalalignment='left',
                       verticalalignment='top', fontsize=8, color='#555555')
    if len(inputdict['includeLetAgreed'])>0:
        ax[0].annotate('Incl. let agreed:', xy=(0.022, 0.76), xycoords='figure fraction', horizontalalignment='left',
                       verticalalignment='top', fontsize=8, color='#555555')
        ax[0].annotate(str(inputdict['includeLetAgreed']), xy=(0.17, 0.76), xycoords='figure fraction', horizontalalignment='left',
                       verticalalignment='top', fontsize=8, color='#555555')


    ax[0].annotate('Results summary', xy=(0.022, 0.72), xycoords='figure fraction', horizontalalignment='left',
                   verticalalignment='top', fontsize=8, color='#555555', fontweight='bold')
    ax[0].annotate('No. of reported properties:', xy=(0.022, 0.70), xycoords='figure fraction',
                   horizontalalignment='left', verticalalignment='top', fontsize=8, color='#555555')
    ax[0].annotate(no_of_total_results, xy=(0.17, 0.70), xycoords='figure fraction',
                   horizontalalignment='left', verticalalignment='top', fontsize=8, color='#555555')
    ax[0].annotate('No. of initial results:', xy=(0.022, 0.68), xycoords='figure fraction', horizontalalignment='left',
                   verticalalignment='top', fontsize=8, color='#555555')
    ax[0].annotate(len(rm.index), xy=(0.17, 0.68), xycoords='figure fraction', horizontalalignment='left',
                   verticalalignment='top', fontsize=8, color='#555555')
    ax[0].annotate('No. of final results:', xy=(0.022, 0.66), xycoords='figure fraction',
                   horizontalalignment='left', verticalalignment='top', fontsize=8, color='#555555')
    ax[0].annotate(str(len(curated_data.index))+' ({0:.0f}%)'.format(100*len(curated_data.index)/no_of_total_results), xy=(0.17, 0.66), xycoords='figure fraction',
                   horizontalalignment='left', verticalalignment='top', fontsize=8, color='#555555')
    ax[0].annotate('No. of wards:', xy=(0.022, 0.64), xycoords='figure fraction',
                   horizontalalignment='left', verticalalignment='top', fontsize=8, color='#555555')
    ax[0].annotate(len(avg_ward_prices.index), xy=(0.17, 0.64), xycoords='figure fraction',
                   horizontalalignment='left', verticalalignment='top', fontsize=8, color='#555555')
    ax[0].annotate('No. of districts:', xy=(0.022, 0.62), xycoords='figure fraction',
                   horizontalalignment='left', verticalalignment='top', fontsize=8, color='#555555')
    ax[0].annotate(len(avg_district_prices.index), xy=(0.17, 0.62), xycoords='figure fraction',
                   horizontalalignment='left', verticalalignment='top', fontsize=8, color='#555555')
    ax[0].annotate('Median price:', xy=(0.022, 0.60), xycoords='figure fraction',
                   horizontalalignment='left', verticalalignment='top', fontsize=8, color='#555555')
    ax[0].annotate('£'+str(int(np.median(curated_data['price']))), xy=(0.17, 0.60), xycoords='figure fraction',
                   horizontalalignment='left', verticalalignment='top', fontsize=8, color='#555555')

    ax[0].annotate('Top results', xy=(0.18, 0.37), xycoords='figure fraction', horizontalalignment='left',
                   verticalalignment='top', fontsize=10, color='#555555', fontweight='bold')
    plt.subplots_adjust(left=0.17, bottom=0.09, right=0.95, top=0.9)

    #   output files' formats
    plotdirs = {'pdf': 'output/' + str(datetime.now())[:10] + '_' + str(inputdict['minprice']) + '_' + str(inputdict['maxprice']) +'_'+ str(inputdict['min_number_bedrooms']) + '_' + str(inputdict['max_number_bedrooms']) + '_'  + '_' + str(inputdict['propertytype']) + '.pdf',
                'jpeg': 'output/' + str(datetime.now())[:10] + '_' + str(inputdict['minprice']) + '_' + str(inputdict['maxprice']) +'_'+ str(inputdict['min_number_bedrooms']) + '_' + str(inputdict['max_number_bedrooms']) + '_'  + '_' + str(inputdict['propertytype']) + '.jpeg'}

    print('Saving figures to the following directories:')
    print('\t'+plotdirs['jpeg'])
    plt.savefig(plotdirs['jpeg'], dpi=200, bbox_inches='tight',edgecolor='black')
    print('\t'+plotdirs['pdf'])
    plt.savefig(plotdirs['pdf'], dpi=200, bbox_inches='tight', edgecolor='black')

    # timer measures the time from beginning to the plot saving
    global timer2
    timer2 = datetime.now()

map_df, post_extracted_data = load_local_data('data/city/London/London_Ward_CityMerged.shp','data/city/London/London_postcodes_lite.csv')
inputdict = user_input()
timer1 = datetime.now()
rm, no_of_total_results = rightmove_scraper()
retrieved_postcodes = postcode_search()
final_map_df,mapped_wards, avg_ward_prices, avg_district_prices, curated_data, highest_dist = result_analyser()

datasaver()
map_plotter()
print('Processing time: ',timer2-timer1)