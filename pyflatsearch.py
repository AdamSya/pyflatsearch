import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
from rightmove_webscraper import rightmove_data
import re
import urllib.request
from time import sleep
from datetime import datetime
p= 1
# show all dataframe columns in print
pd.set_option('display.expand_frame_repr', False)

def user_input():
    """Attributes to search on Rightmove"""
    price = 500
    radius = 5.0  # decimal (1dp)
    proptype = 'flat'
    number_bedrooms = 1

    # price = input('Property upper price limit (integer): ')
    # radius = input('Search area radius (mi; integer): ')
    # proptype = input('Property type: ').lower()
    # proptype_dict = {'house': 'Houses', 'flat': 'flats', 'bungalow': 'bungalow', 'land': 'land',
    #                      'park home': 'park-home', 'student halls': 'private-halls'}
    # if proptype in proptype_dict:
    #     proptype = proptype_dict[proptype]
    # number_bedrooms = input('Number of bedrooms: ')

    return price,radius,proptype,number_bedrooms

def load_local_data(map_file, postcode_file):
    """Load local data i.e. shp map file and the list of postcodes"""

    # Load the map of London in shp and shx format (both required)
    shp_map = map_file
    map_df = gpd.read_file(shp_map)
    print('Loaded the map of London: '+map_file)

    # Load a list of London postcodes
    postcode_district = pd.read_csv(postcode_file)

    # if postcode_file_tuple is tuple:
    #     for i in range(1,len(postcode_file_tuple)):
    #         print(postcode_file_tuple[i])
    #         postcode_district = postcode_district.append(pd.read_csv(postcode_file_tuple[i]))

    print(postcode_district)
    post_dist_f = postcode_district[['Postcode','Ward']].reset_index()
    print('Loaded London postcodes: ' + str(postcode_file))

    print(post_dist_f)
    return map_df,post_dist_f


def rightmove_scraper():
    """The function uses package rightmove_webscraper"""

    # Load the properties using rightmove_webscraper package
    print('Loading the current property data from Rightmove...')
    url = "https://www.rightmove.co.uk/property-to-rent/" \
      "find.html?locationIdentifier=REGION%5E87490&"+"maxPrice=%d&" % price + \
          "radius=%.1f&" % radius + \
          "propertyTypes=%s&" % proptype + \
          "maxBedrooms=%d&minBedrooms=%d&" % (number_bedrooms,number_bedrooms) + \
          "primaryDisplayPropertyType=flats&includeLetAgreed=false"
    rightmove_object = rightmove_data(url)
    rm = rightmove_object.get_results
    print('Property data loaded (%d properties).' % len(rm.index))
    return rm

def postcode_search():
    """Search rightmove HTML page sources for post codes"""
    print('Retrieving property postcodes... Please wait (up to '+ "{0:.1f}".format(len(rm.index)/60) +' minute(s))...')
    retrieved_postcodes = []
    for url in rm['url']:
        op = urllib.request.urlopen(url)
        read_url = op.read()
        try:
            retrieved_postcodes.append(re.findall('"postcode":"(.*?)"', str(read_url))[0])
        except:
            retrieved_postcodes.append(np.nan)
        sleep(0.1)
    print('%d property postcodes retrieved' % len(retrieved_postcodes))
    return retrieved_postcodes

def result_analyser():
    """Formats the dataframe to remove unnecessary data"""

    # remove unnecessary column
    rmfiltered = rm.drop(['type','agent_url','search_date','url','postcode','number_bedrooms'], axis=1)

    # add a column containing the retrieved full postcodes
    rmfiltered['postcode'] = retrieved_postcodes

    # drop properties lacking crucial info
    curated_properties = rmfiltered.dropna()

    # search the wards using the post code and add to the dataframe
    curated_districts = []
    for postcode in curated_properties['postcode']:
        temp = post_dist_f[post_dist_f['Postcode'].str.startswith(postcode)]
        try:
            curated_districts.append(temp['Ward'].values[0])
        except:
            curated_districts.append(np.nan)
    curated_properties['ward'] = curated_districts
    curated_properties = curated_properties.dropna()
    print(curated_properties)

    # obtain average prices per ward in London in a dataframe format
    avg_prices = curated_properties['ward','price'].groupby('ward').mean()
    std_prices = curated_properties['ward','price'].groupby('ward').agg(np.std,ddof=0)

    print(std_prices)
    # merge the average price dataframe with the map dataframe
    # also create a list with tuples of ward name, ward abv, and average property price
    avg_list = []
    ward_abvs = []
    ward_tuples = []
    for index, row in map_df.iterrows():
        if row['NAME'] in avg_prices.index.values:
            avg_list.append(avg_prices.loc[row['NAME'],'price'])
            ward_abvs.append(''.join([c for c in row['NAME'] if c.isupper()]))
            ward_tuples.append((row['NAME'],''.join([c for c in row['NAME'] if c.isupper()]),avg_prices.loc[row['NAME'],'price']))
        else:
            avg_list.append(0)
            ward_abvs.append('')

    map_df['average_prices'] = avg_list
    map_df['ward_abvs'] = ward_abvs

    return map_df,avg_list,ward_tuples,avg_prices, curated_properties

def datasaver():
    ward_avg_prices.to_csv('output/'+str(datetime.now())[:10]+'_'+str(price)+'_'+proptype+'_summary.csv')
    curated_properties.to_csv('output/'+str(datetime.now())[:10]+'_'+str(price)+'_'+proptype+'_full.csv')

def map_plotter(dataframe):
    fig, ax = plt.subplots(1, figsize=(8, 7))
    fig.tight_layout()
    fig.patch.set_facecolor('#f2f2f2')

    # set colormap
    cmap = plt.cm.Reds
    cmap.set_under(color='white')
    vmin = sorted(set(avg_list))[1]-50
    vmax = max(avg_list)

    # add a title
    ax.set_title('Property prices in London\n(%d-bed, Up to £%dpcm, %ss)' % (number_bedrooms,price,proptype),fontsize=16,fontweight='bold')

    # create an annotation for the data source
    ax.annotate('Source: Rightmove (%s; %d properties in %d wards)' % (str(datetime.now())[:10],len(rm.index),len(ward_avg_prices.index)),
                xy=(0.1, .08),  xycoords='figure fraction', horizontalalignment='left', verticalalignment='top', fontsize=8, color='#555555')

    # remove axes
    ax.axis('off')

    dataframe.plot(linewidth=0.8, ax=ax, edgecolor='0.8',column=map_df['average_prices'],cmap=cmap,vmin=vmin,vmax=vmax)

    # set up the colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
    sm._A = []
    fig.colorbar(sm,format='£%.0f')

    plt.savefig('output/'+str(datetime.now())[:10]+'_'+str(price)+'_'+str(proptype)+'.png',dpi=400)
    plt.show()

map_df,post_dist_f = load_local_data('data/London_Ward_CityMerged.shp','data/London_postcodes_lite.csv')
price,radius,proptype,number_bedrooms = user_input()
rm = rightmove_scraper()
retrieved_postcodes = postcode_search()
final_map_df,avg_list,ward_tuples, ward_avg_prices, curated_properties = result_analyser()
datasaver()
map_plotter(final_map_df)