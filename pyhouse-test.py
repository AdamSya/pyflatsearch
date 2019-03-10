import pandas as pd
import numpy as np
from shapely.ops import cascaded_union
import geopandas as gpd
from rightmove_webscraper import rightmove_data
import re
import urllib.request
from time import sleep
from datetime import datetime
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
pd.set_option('display.expand_frame_repr', False)
from descartes import PolygonPatch

def user_input():
    """Attributes to search on Rightmove"""
    price = 500 #integer
    radius = 5.0  # decimal (1dp)
    propertytype = 'flat' #dict below
    number_bedrooms = 1 #integer; 0 = studio.

    # while True:
    #     price = input('Property upper price limit (integer): ')
    #     try:
    #         if isinstance(int(price),int):
    #             price = int(price)
    #         break
    #     except:
    #         print('Please type in the upper price limit in pounds (e.g. £1000 as 1000).')
    #
    # while True:
    #     radius = input('Search area radius (mi; integer): ')
    #     try:
    #         if isinstance(int(radius),int):
    #             radius = int(radius)
    #         break
    #     except:
    #         print('Please type in the search radius in miles (e.g. 5 miles as 5).')
    #
    # proptype_dict = {'house': 'Houses', 'flat': 'flat', 'bungalow': 'bungalow', 'land': 'land',
    #                  'park home': 'park-home', 'student halls': 'private-halls'}
    #
    # while True:
    #     proptype = input('Property type ' + str([i for i in proptype_dict]) + ':').lower()
    #     if proptype in proptype_dict:
    #         proptype = proptype_dict[proptype]
    #         break
    #
    # while True:
    #     number_bedrooms = input('Number of bedrooms: ')
    #     try:
    #         if isinstance(int(number_bedrooms),int):
    #             number_bedrooms = int(number_bedrooms)
    #         break
    #     except:
    #         print('Please type in the number of bedrooms (e.g. 2-bedroom property as 2).')

    return price,radius,propertytype,number_bedrooms

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
    """The function uses package rightmove_webscraper to mine data from RightMove.co.uk"""

    #   Load the properties using rightmove_webscraper package
    #   Limit of 1050 properties imposed by the website design
    url = "https://www.rightmove.co.uk/property-to-rent/" \
      "find.html?locationIdentifier=REGION%5E87490&"+"maxPrice=%d&" % price + \
          "radius=%.1f&" % radius + \
          "propertyTypes=%s&" % proptype + \
          "maxBedrooms=%d&minBedrooms=%d&" % (number_bedrooms,number_bedrooms) + \
          "primaryDisplayPropertyType=flats&includeLetAgreed=false"
    print('Loading the current property data from Rightmove: '+str(url))
    rightmove_object = rightmove_data(url)
    rm_scraper_data = rightmove_object.get_results
    if len(rm_scraper_data.index) >= 1050:
        print('Property data loaded (%d properties). Sample size limit of 1050 has been reached.' % len(rm_scraper_data.index))
    else:
        print('Property data loaded (%d properties).' % len(rm_scraper_data.index))
    #   experimentally derived line of best fit for the completion time based on number of results
    e = (len(rm_scraper_data.index)+12.887414891936531)/2.0802669077254334
    print('Estimated total processing time: %d min %d sec.' % (int(str(e/60)[0]),int(e%60)))

    return rm_scraper_data

def postcode_search():
    """Search rightmove HTML page sources for post codes"""
    print('Retrieving property postcodes... Please wait (approx. '+ "{0:.1f}".format(0.4*len(rm.index)/60) +' minute(s))...')
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
    curated_data.columns = ['price', 'address', 'postcode', 'index', 'ward', 'district',
       'distance', 'lat', 'long']
    print('#####'*20)
    print(curated_data)

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

    return map_df,mapped_wards, avg_ward_prices, avg_district_prices, curated_data,highest_dist

def datasaver():
    """Saves the data as csv"""

    #   saves a summary report with ward average prices
    avg_ward_prices.to_csv('output/'+str(datetime.now())[:10]+'_'+str(price)+'_'+str(number_bedrooms)+'_'+proptype+'_summary.csv')
    curated_data.to_csv('output/'+str(datetime.now())[:10]+'_'+str(price)+'_'+str(number_bedrooms)+'_'+proptype+'_full.csv')

def map_plotter(dataframe):
    fig, ax = plt.subplots(2,1, figsize=(10, 7.5),gridspec_kw={'height_ratios':[2, 1]})
    fig.tight_layout(pad=1, w_pad=0.5, h_pad=0.5)
    fig.patch.set_facecolor('#f2f2f2')

    # set colormap
    cmap = plt.cm.Reds
    cmap.set_under(color='white')

    # vmin = sorted(set(ward_avg_prices['price']))[1]-10
    vmin = min(avg_ward_prices['price'])
    vmax = max(avg_ward_prices['price'])
    xmin = lambda x: round(vmin, -2) - 100 if round(vmin, -2) > vmin else round(vmin, -2)
    xmax = lambda x: round(vmax, -2) + 100 if round(vmax, -2) < vmax else round(vmax, -2)
    xmin = xmin(xmin)
    xmax = xmax(vmax)

    #   add a title...
    ax[0].set_title('Rental property pricing in London\n',fontsize=16,fontweight='bold', color='#333333')
    #   and subtitle...
    ax[0].annotate('(%d-bed, up to £%dpcm, property type: %s)' % (number_bedrooms,price,proptype),xy=(.5, .92),ha='center',fontsize=10,  xycoords='figure fraction', verticalalignment='top', color='#555555',zorder=200)

    # create an annotation for the data source
    ax[0].annotate('Source: Rightmove (%s; %d properties in %d wards in %d districts).' % (str(datetime.now())[:10],len(curated_data.index),len(avg_ward_prices.index),len(avg_district_prices.index)),
                xy=(0.01, .02),  xycoords='figure fraction', horizontalalignment='left', verticalalignment='top', fontsize=8, color='#555555')
    ax[0].set_xlim([500000, 563000])
    ax[0].set_ylim([155000, 202000])
    # remove axes
    ax[0].axis('off')

    plt.setp(ax[1].lines, zorder=50)
    plt.setp(ax[1].collections, zorder=50, label="")

    # positives = dataframe[dataframe['average_prices']>0]
    # positives = dataframe['average_prices'].apply(lambda x: np.nan if x==0 else x)
    # # print(positives)
    # dataframe['average_prices'] = positives
    # print(dataframe)

    # print(mapped_wards)
    #   use the ward results and obtain the centre of polygon for each ward
    map_pos_wards = mapped_wards[['DISTRICT', 'geometry', 'price']]
    map_pos_wards = map_pos_wards[map_pos_wards['price'] != 0]
    centrx = map_pos_wards['geometry'].apply(lambda c: c.centroid.x)
    centry = map_pos_wards['geometry'].apply(lambda c: c.centroid.y)


    # print(curated_properties)

    j_map = cascaded_union(map_pos_wards['geometry'])
    j = ax[0].add_patch(PolygonPatch(j_map,fc='none', ec='#c1c1c1'))


    # print('HERE!')
    # print(map_df)
    # print()
    sns.kdeplot(centrx, centry, ax=ax[0], n_levels=50, cmap=cmap, shade=True, shade_lowest=False,
                zorder=11, kernel='biw', gridsize=1000, alpha=1)
    # sns.kdeplot(curated_properties['lat'], curated_properties['long'], ax=ax[0], n_levels=50, cmap=cmap, shade=True, shade_lowest=False,
    #             zorder=11, kernel='biw', gridsize=1000, alpha=1)
    for col in ax[0].collections:
        col.set_clip_path(j)

    map_df.plot(linewidth=0.5, ax=ax[0], edgecolor='#c1c1c1',color='white')
    map_pos_wards.plot(linewidth=0.8, ax=ax[0], edgecolor='#c1c1c1', column=map_pos_wards['price'], vmin=xmin, vmax=xmax,
                   cmap=cmap, zorder=10)

    ax[0].add_patch(PolygonPatch(j_map, fc='none', ec='#c1c1c1'))

    # set up the colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=xmin, vmax=xmax))
    sm._A = []
    fig.colorbar(sm,format='£%.0f',ax=ax[0])

    sns.set(style="whitegrid")
    # set_dist = set(curated_properties['district'])
    selected_properties = curated_data[curated_data.district.isin(highest_dist)].sort_values(by='district')

    # selected_properties = selected_properties[selected_properties['district'] == 'Merton']

    plot_markersize = [10+2*10**(1-(a-min(selected_properties['distance'])/max(selected_properties['distance'])/min(selected_properties['distance']))) for a in selected_properties['distance']]
    print(plot_markersize)
    # sns.stripplot(x="price", y="district", hue='district',
    #               data=selected_properties,
    #               vmin=vmin, vmax=xmax,
    #               jitter=False, alpha=0.8, edgecolor="black", zorder=10,scatter_kws={'s':plotsize})
    sns.scatterplot(x="price", y="district", hue='district',
                  data=selected_properties,
                  alpha=0.6, edgecolor='none',zorder=10, s=plot_markersize)



    barplotdata = selected_properties[['district','price']]
    new_bar = selected_properties[['district','price']].groupby('district').min()
    new_bar['min'] = barplotdata.groupby('district')['price'].min().values
    new_bar['max'] = barplotdata.groupby('district')['price'].max().values
    new_bar['avg'] = barplotdata.groupby('district')['price'].mean().values
    new_bar['avg'] = new_bar['avg'][new_bar['avg'] != new_bar['min']]

    print(new_bar)
    print(selected_properties[['district','price']])
    print(selected_properties[selected_properties['district']=='Barnet'])

    sns.barplot(x='max', y=new_bar.index, data=new_bar,
                 label="Total", alpha=0.5,ci=None,zorder=2, )
    sns.barplot(x='min', y=new_bar.index, data=new_bar,
                label="Total", color="white",zorder=3)

    ax[1].get_legend().remove()

    sns.pointplot(size=5,x=new_bar['avg'], y=new_bar.index,
                  data=new_bar, join=False, markers=["|"], palette=['black'],zorder=5000) #sns.color_palette("hls", len(new_bar.index)) #sns.hls_palette(8, l=.3, s=.8))

    # ax[1].grid(b=True, which='major', color='#f2f2f2', linewidth=5,zorder=1)
    # ax[1].grid(b=True, which='minor', color='b', linewidth=0.5)
    # sns.set_context(rc={"grid.linewidth": 4})
    ax[1].set_xlabel('Price', fontsize=10, color='#555555')
    ax[1].set_ylabel('District', fontsize=10, color='#555555')
    ax[1].set_xlim([xmin, xmax])

    plt.xticks(fontsize=8, rotation=90)
    ax[1].xaxis.set_major_formatter(FormatStrFormatter('£%.0f'))
    ax[1].xaxis.grid(False)

    plt.yticks(fontsize=8)

    plt.savefig('output/'+str(datetime.now())[:10]+'_'+str(price)+'_'+str(proptype)+'.png',dpi=400)
    global timer2
    timer2 = datetime.now()
    plt.subplots_adjust(left=0.2, bottom=0.09, right=0.86, top=0.9)
    plt.show()

map_df, post_extracted_data = load_local_data('data/city/London/London_Ward_CityMerged.shp','data/city/London/London_postcodes_lite.csv')
price,radius,proptype,number_bedrooms = user_input()
timer1 = datetime.now()
rm = rightmove_scraper()
retrieved_postcodes = postcode_search()
final_map_df,mapped_wards, avg_ward_prices, avg_district_prices, curated_data, highest_dist = result_analyser()

datasaver()
map_plotter(final_map_df)
print('Processing time: ',timer2-timer1)
pd.set_option('display.expand_frame_repr', False)
a = pd.read_csv('data/London postcodes.csv')


# # b = a.iloc[:int(a.shape[0]/2),:]
# # # print(b)
# # #
# # # c = a.iloc[int(a.shape[0]/2):,:]
# # # print(c)
# print(a.columns)
# print(a[['Nearest station', 'Distance to station']])
# b = a[['Postcode','Ward']]
# print(b)

