import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
from rightmove_webscraper import rightmove_data
import re
import urllib.request
from time import sleep
from datetime import datetime
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
p= 1
# show all dataframe columns in print
pd.set_option('display.expand_frame_repr', False)

def user_input():
    """Attributes to search on Rightmove"""
    price = 600
    radius = 5.0  # decimal (1dp)
    proptype = 'house'
    number_bedrooms = 1

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
    post_dist_f = postcode_district[['Postcode','Ward','District','Distance to station']].reset_index()
    print('Loaded London postcodes: ' + str(postcode_file))
    return map_df,post_dist_f


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

    print('Loading the current property data from Rightmove: '+str(url))
    rightmove_object = rightmove_data(url)
    rm = rightmove_object.get_results
    print('Property data loaded (%d properties).' % len(rm.index))
    e = (len(rm.index)+12.887414891936531)/2.0802669077254334 #experimentally derived line of best fit
    print('Estimated total processing time: %d min %d sec.' % (int(str(e/60)[0]),int(e%60)))
    rightmove_object = rightmove_data(url)
    rm = rightmove_object.get_results
    print('Property data loaded (%d properties).' % len(rm.index))
    return rm

def postcode_search():
    """Search rightmove HTML page sources for post codes"""
    print('Retrieving property postcodes... Please wait (approx. '+ "{0:.1f}".format(0.4*len(rm.index)/60) +' minute(s))...')

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

    print('%d property postcodes retrieved.' % len(retrieved_postcodes))
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
    print(curated_properties)

    # search the wards using the post code and add to the dataframe
    curated_wards = []
    curated_districts = []
    curated_distance = []
    for postcode in curated_properties['postcode']:
        temp = post_dist_f[post_dist_f['Postcode'].str.startswith(postcode)]
        try:
            curated_wards.append(temp['Ward'].values[0])
        except:
            curated_wards.append(np.nan)
        try:
            curated_districts.append(temp['District'].values[0])
        except:
            curated_districts.append(np.nan)
        try:
            curated_distance.append(temp['Distance to station'].values[0])
        except:
            curated_distance.append(np.nan)

    curated_properties['ward'] = curated_wards
    curated_properties['district'] = curated_districts
    curated_properties['distance'] = curated_distance

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
    avg_prices = curated_properties[['district','ward','price']].groupby('ward').mean()
    district_prices = curated_properties[['district','ward','price']].groupby('district').mean()
    highest_dist = curated_properties[['district','ward','price']].groupby('district').count().sort_values(by='ward',ascending=False)
    highest_dist = highest_dist.index[:(min(len(highest_dist),15))]

    avg_list = []
    for index, row in map_df.iterrows():
        if row['NAME'] in avg_prices.index.values:
            avg_list.append(avg_prices.loc[row['NAME'],'price'])
        else:
            avg_list.append(0)

    map_df['average_prices'] = avg_list
    return map_df,avg_list,avg_prices, curated_properties,district_prices, highest_dist

def datasaver():
    """Saves the data as csv"""
    ward_avg_prices.to_csv('output/'+str(datetime.now())[:10]+'_'+str(price)+'_'+str(number_bedrooms)+'_'+proptype+'_summary.csv')
    curated_properties.to_csv('output/'+str(datetime.now())[:10]+'_'+str(price)+'_'+str(number_bedrooms)+'_'+proptype+'_full.csv')

def map_plotter(dataframe):
    fig, ax = plt.subplots(2,1, figsize=(12, 7.5),gridspec_kw={'height_ratios':[2, 1]})
    # fig.tight_layout()
    fig.patch.set_facecolor('#f2f2f2')
    plt.subplots_adjust(left=0.1)
    # set colormap
    cmap = plt.cm.Reds
    # cmap = sns.cubehelix_palette(start=2.8, rot=.1)
    cmap.set_under(color='white')
    vmin = sorted(set(avg_list))[1]-10
    vmax = max(avg_list)
    xmax = lambda x: round(vmax, -2) + 100 if round(vmax, -2) < vmax else round(vmax, -2)
    xmin = lambda x: round(vmin, -2) - 100 if round(vmin, -2) > vmin else round(vmin, -2)
    xmax = xmax(vmax)
    xmin = xmin(xmin)


    # add a title
    ax[0].set_title('Rental property pricing in London\n(%d-bed, Up to £%dpcm, %ss)' % (number_bedrooms,price,proptype),fontsize=16,fontweight='bold',**{'fontname':'Tahoma'})

    # create an annotation for the data source
    ax[0].annotate('Source: Rightmove (%s; %d properties in %d wards in %d districts).' % (str(datetime.now())[:10],len(curated_properties.index),len(ward_avg_prices.index),len(district_prices.index)),
                xy=(0.01, .008),  xycoords='figure fraction', horizontalalignment='left', verticalalignment='top', fontsize=8, color='#555555')

    # remove axes
    ax[0].axis('off')

    plt.setp(ax[1].lines, zorder=50)
    plt.setp(ax[1].collections, zorder=50, label="")



    # positives = dataframe[dataframe['average_prices']>0]
    # positives = dataframe['average_prices'].apply(lambda x: np.nan if x==0 else x)
    # # print(positives)
    # dataframe['average_prices'] = positives
    # print(dataframe)
                                                        #this.
    # dataframe.plot(linewidth=0.8, ax=ax[0], edgecolor='0.8', color='white')
    dataframe.plot(linewidth=0.8, ax=ax[0], edgecolor='gray',column=dataframe['average_prices'],cmap=cmap,vmin=xmin,vmax=xmax)


    # set up the colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=xmin, vmax=xmax))
    sm._A = []
    fig.colorbar(sm,format='£%.0f',ax=ax[0])



    sns.set(style="whitegrid")
    # sns.despine()
    # tips = sns.load_dataset(curated_properties)

    set_dist = set(curated_properties['district'])
    selected_properties = curated_properties[curated_properties.district.isin(highest_dist)].sort_values(by='district')

    # selected_properties = selected_properties[selected_properties['district'] == 'Merton']
    print(selected_properties)

    plotsize = [10+2*10**(1-(a-min(selected_properties['distance'])/max(selected_properties['distance'])/min(selected_properties['distance']))) for a in selected_properties['distance']]
    print(plotsize)
    # sns.stripplot(x="price", y="district", hue='district',
    #               data=selected_properties,
    #               vmin=vmin, vmax=xmax,
    #               jitter=False, alpha=0.8, edgecolor="black", zorder=10,scatter_kws={'s':plotsize})
    sct = sns.scatterplot(x="price", y="district", hue='district',
                  data=selected_properties,
                  alpha=0.6, edgecolor='none',zorder=10, s=plotsize)



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
    ax[1].set_xlabel('Price', fontsize=10)
    ax[1].set_ylabel('District', fontsize=10)
    ax[1].set_xlim([xmin, xmax])

    plt.xticks(fontsize=8, rotation=90)
    ax[1].xaxis.set_major_formatter(FormatStrFormatter('£%.0f'))
    ax[1].xaxis.grid(False)

    plt.yticks(fontsize=8)

    plt.savefig('output/'+str(datetime.now())[:10]+'_'+str(price)+'_'+str(proptype)+'.png',dpi=400)
    global timer2
    timer2 = datetime.now()
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

map_df,post_dist_f = load_local_data('data/city/London/London_Ward_CityMerged.shp','data/city/London/London_postcodes_lite.csv')
price,radius,proptype,number_bedrooms = user_input()
timer1 = datetime.now()
rm = rightmove_scraper()

retrieved_postcodes = postcode_search()


final_map_df,avg_list, ward_avg_prices, curated_properties, district_prices, highest_dist = result_analyser()
datasaver()
map_plotter(final_map_df)
print(timer2-timer1)

rm = rightmove_scraper()
retrieved_postcodes = postcode_search()
final_map_df,avg_list,ward_tuples, ward_avg_prices, curated_properties = result_analyser()
datasaver()
map_plotter(final_map_df)

