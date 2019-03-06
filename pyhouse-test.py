import pandas as pd
pd.set_option('display.expand_frame_repr', False)
a = pd.read_csv('data/London postcodes.csv')

# b = a.iloc[:int(a.shape[0]/2),:]
# # print(b)
# #
# # c = a.iloc[int(a.shape[0]/2):,:]
# # print(c)

print(a.columns)

print(a[['Nearest station', 'Distance to station']])

b = a[['Postcode','Ward']]
print(b)

b.to_csv('London_postcodes_lite.csv')