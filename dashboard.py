# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import pandas as pd 
import numpy as np 
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import warnings
warnings.filterwarnings('ignore')
from datetime import datetime

def style_negative(v, props=''):
    try:
        return props if v < 0 else None
    except:
        pass

def style_positive(v, props=''):
    try:
        return props if v > 0 else None
    except:
        pass    

def audience_simple(country):
    if country == 'US':
        return 'USA'
    elif country == 'IN':
        return 'India'
    else:
        return 'Other'
 
st.set_page_config(layout='wide')
st.title('Analysis of Ken Jee\'s performance')
    
def load_data():
    """ Loads in 4 dataframes and does light feature engineering"""
    df_agg = pd.read_csv('Aggregated_Metrics_By_Video.csv').iloc[1:,:]
    df_agg.columns = ['Video','Video title','Video publish time','Comments added','Shares','Dislikes','Likes',
                      'Subscribers lost','Subscribers gained','RPM(USD)','CPM(USD)','Average % viewed','Average view duration',
                      'Views','Watch time (hours)','Subscribers','Your estimated revenue (USD)','Impressions','Impressions ctr(%)']
    df_agg['Video publish time'] = pd.to_datetime(df_agg['Video publish time'], format = '%b %d, %Y')
    df_agg['Average view duration'] = df_agg['Average view duration'].apply(lambda x: datetime.strptime(x,'%H:%M:%S'))
    df_agg['Avg_duration_sec'] = df_agg['Average view duration'].apply(lambda x: x.second + x.minute*60 + x.hour*3600)
    df_agg['Engagement_ratio'] =  (df_agg['Comments added'] + df_agg['Shares'] +df_agg['Dislikes'] + df_agg['Likes']) /df_agg.Views
    df_agg['Views / sub gained'] = df_agg['Views'] / df_agg['Subscribers gained']
    df_agg.sort_values('Video publish time', ascending = False, inplace = True)    
    df_agg_sub = pd.read_csv('Aggregated_Metrics_By_Country_And_Subscriber_Status.csv')
    df_comments = pd.read_csv('Aggregated_Metrics_By_Video.csv')
    df_time = pd.read_csv('Video_Performance_Over_Time.csv')
    df_time['Date'] = pd.to_datetime(df_time['Date'], format='%d-%m-%Y')
    return df_agg, df_agg_sub, df_comments, df_time 


df_agg, df_agg_sub, df_comments, df_time = load_data()

#additional data engineering for aggregated data
df_agg_diff = df_agg.copy()
df_agg_diff2 = df_agg_diff.copy()

#Just numeric columns 
numeric_cols = np.array((df_agg_diff.dtypes == 'float64') | (df_agg_diff.dtypes == 'int64')) 
df_agg_diff2 = df_agg_diff2.iloc[:,numeric_cols]

metric_date_12mo = df_agg_diff['Video publish time'].max() - pd.DateOffset(months =12)
median_agg = df_agg_diff2[df_agg_diff['Video publish time'] >= metric_date_12mo].median()

#create differences from the median for values 

df_agg_diff.iloc[:,numeric_cols] = (df_agg_diff.iloc[:,numeric_cols] - median_agg).div(median_agg)

df_time_diff = pd.merge(df_time, df_agg.loc[:,['Video','Video publish time']], left_on ='External Video ID', right_on = 'Video')
df_time_diff['days_published'] = (df_time_diff['Date'] - df_time_diff['Video publish time']).dt.days

# get last 12 months of data rather than all data 
date_12mo = df_agg['Video publish time'].max() - pd.DateOffset(months =12)
df_time_diff_yr = df_time_diff[df_time_diff['Video publish time'] >= date_12mo]

# get daily view data (first 30), median & percentiles 
views_days = pd.pivot_table(df_time_diff_yr,index= 'days_published',values ='Views', aggfunc = [np.mean,np.median,lambda x: np.percentile(x, 80),lambda x: np.percentile(x, 20)]).reset_index()
views_days.columns = ['days_published','mean_views','median_views','80pct_views','20pct_views']
views_days = views_days[views_days['days_published'].between(0,30)]
views_cumulative = views_days.loc[:,['days_published','median_views','80pct_views','20pct_views']] 
views_cumulative.loc[:,['median_views','80pct_views','20pct_views']] = views_cumulative.loc[:,['median_views','80pct_views','20pct_views']].cumsum()


add_sidebar = st.sidebar.selectbox('Aggregate or Individual Video', ('Aggregate Metrics', 'Individual Video Analysis', 'Top 10 Analysis'))

if add_sidebar == 'Aggregate Metrics':
    df_agg_metrics = df_agg[['Video publish time','Views','Likes','Subscribers','Shares','Comments added','RPM(USD)','Average % viewed',
                             'Avg_duration_sec', 'Engagement_ratio','Views / sub gained']]
    metric_date_6mo = df_agg_metrics['Video publish time'].max() - pd.DateOffset(months =6)
    metric_date_12mo = df_agg_metrics['Video publish time'].max() - pd.DateOffset(months =12)
    metric_medians6mo = df_agg_metrics[df_agg_metrics['Video publish time'] >= metric_date_6mo].median()
    metric_medians12mo = df_agg_metrics[df_agg_metrics['Video publish time'] >= metric_date_12mo].median()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    columns = [col1, col2, col3, col4, col5]
    
    count = 0
    for i in metric_medians6mo.iloc[1:].index:
        with columns[count]:
            delta = (metric_medians6mo[i] - metric_medians12mo[i])/metric_medians12mo[i]
            st.metric(label= i, value = round(metric_medians6mo[i],1), delta = "{:.2%}".format(delta))
            count += 1
            if count >= 5:
                count = 0
    
    #get date information / trim to relevant data 
    df_agg_diff['Publish_date'] = df_agg_diff['Video publish time'].apply(lambda x: x.date())
    df_agg_diff_final = df_agg_diff.loc[:,['Video title','Publish_date','Views','Likes','Subscribers','Shares','Comments added','RPM(USD)','Average % viewed',
                             'Avg_duration_sec', 'Engagement_ratio','Views / sub gained']]
    
    numeric_cols_2 = np.array((df_agg_diff_final.dtypes == 'float64') | (df_agg_diff_final.dtypes == 'int64'))                
    df_agg_numeric_lst = df_agg_diff_final.iloc[:,numeric_cols_2]
    df_to_pct = {}
    for i in df_agg_numeric_lst:
        df_to_pct[i] = '{:.1%}'.format
    st.dataframe(df_agg_diff_final.style.applymap(style_negative, props = 'color:red').applymap(style_positive, props = 'color:green').format(df_to_pct))

    df_agg_year = df_agg.copy()
    df_agg_year['Year'] = df_agg_year['Video publish time'].dt.year
    
    df_yearly_videos = df_agg_year.groupby('Year')['Video'].count().reset_index()
    
    highlight_title = '2020'
    fig = px.bar(df_yearly_videos, x = 'Year', y = 'Video', labels = {'Video': 'Number of Videos'}, title='Videos by Year')
    fig.update_traces(marker_color=['green' if year == highlight_title else 'blue' for year in fig.data[0].x.tolist()])
    st.plotly_chart(fig)
    
    st.write("As we can clearly see, 2020 stands head and shoulder above all others doubling the second highest video per year count in 2019. Starting from 2019, Ken Jee have increased his involvment in content creation dramatically, perhaps signalling his checkpoint for the devotion for Youtube.")
    
if add_sidebar == 'Individual Video Analysis':
    video = tuple(df_agg['Video title'])
    video_select = st.selectbox('Pick A Video: ', video)
    
    agg_filtered = df_agg[df_agg['Video title'] == video_select]
    agg_sub_filtered = df_agg_sub[df_agg_sub['Video Title'] == video_select]
    agg_sub_filtered['Country'] = agg_sub_filtered['Country Code'].apply(audience_simple)
    agg_sub_filtered.sort_values('Is Subscribed', inplace = True)
    
    fig = px.bar(agg_sub_filtered, x = 'Views', y = 'Is Subscribed', color = 'Country', orientation = 'h')
    st.plotly_chart(fig)
    
    agg_time_filtered = df_time_diff[df_time_diff['Video Title'] == video_select]
    first_30 = agg_time_filtered[agg_time_filtered['days_published'].between(0,30)]
    first_30 = first_30.sort_values('days_published')
    
    
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=views_cumulative['days_published'], y=views_cumulative['20pct_views'],
                    mode='lines',
                    name='20th percentile', line=dict(color='purple', dash ='dash')))
    fig2.add_trace(go.Scatter(x=views_cumulative['days_published'], y=views_cumulative['median_views'],
                        mode='lines',
                        name='50th percentile', line=dict(color='black', dash ='dash')))
    fig2.add_trace(go.Scatter(x=views_cumulative['days_published'], y=views_cumulative['80pct_views'],
                        mode='lines', 
                        name='80th percentile', line=dict(color='royalblue', dash ='dash')))
    fig2.add_trace(go.Scatter(x=first_30['days_published'], y=first_30['Views'].cumsum(),
                        mode='lines', 
                        name='Current Video' ,line=dict(color='firebrick',width=8)))
    fig2.update_layout(title = 'View comparison first 30 days',
                        xaxis_title = 'Days Since Published',
                        yaxis_title = 'Cumulative views')
    
    st.plotly_chart(fig2)

if add_sidebar == 'Top 10 Analysis':
    col1, col2 = st.columns(2)
    df_agg_sub_sum = df_agg_sub.groupby('Video Title').agg({
    'Views' : 'sum',
    'Video Likes Added': 'sum',
    'Video Dislikes Added': 'sum',
    'Video Likes Removed': 'sum',
    'User Subscriptions Added': 'sum',
    'User Subscriptions Removed': 'sum'
    }).reset_index()
    df_agg_sub_sum['Total Likes'] = df_agg_sub_sum['Video Likes Added'] - df_agg_sub_sum['Video Likes Removed']
    
    top_views = df_agg_sub_sum.nlargest(10, 'Views')
    top_likes = df_agg_sub_sum.nlargest(10, 'Total Likes')
    top_dislikes = df_agg_sub_sum.nlargest(10, 'Video Dislikes Added')
    top_sub_gain = df_agg_sub_sum.nlargest(10, 'User Subscriptions Added')
    top_sub_lost = df_agg_sub_sum.nlargest(10, 'User Subscriptions Removed')
    
    fig_views = px.bar(top_views, x='Views', y='Video Title', orientation='h', title='Top 10 Videos by Views')
    fig_views.update_traces(marker_color='yellow')
    
    fig_likes = px.bar(top_likes, x='Total Likes', y='Video Title', orientation = 'h', title='Top 10 Most Liked Videos')
    fig_likes.update_traces(marker_color='green')
    
    fig_dislikes = px.bar(top_dislikes, x='Video Dislikes Added', y = 'Video Title', orientation='h', title= 'Top 10 Most Disliked Videos')
    fig_dislikes.update_traces(marker_color='red')
    
    fig_subs_added = px.bar(top_sub_gain, x='User Subscriptions Added', y='Video Title', orientation='h', title='Top 10 Videos by Subscriptions Added')
    fig_subs_added.update_traces(marker_color='blue')
    
    highlight_title = 'Why I Quit Data Science'
    fig_subs_removed = px.bar(top_sub_lost, x='User Subscriptions Removed', y='Video Title', orientation='h', title='Top 10 Videos by Subscriptions Removed')
    fig_subs_removed.update_traces(marker_color=['gray' if title != highlight_title else 'red' for title in fig_subs_removed.data[0].y])
    
    with col1:
        st.plotly_chart(fig_dislikes)
        st.plotly_chart(fig_subs_added)
        st.plotly_chart(fig_views)
    
    with col2:
        st.plotly_chart(fig_likes)
        st.plotly_chart(fig_subs_removed)
        st.write("The video \" How I Would Learn Data Science (If I Had To Start Over)\" is the best performing video, having any where from doubling to nearly quintupling the number of engagement of the second-running up.")
        st.write("An interesting video's metrics is the one titled \" Why I Quit Data Science\" ranking the third highest subscriber lost. This could potentially be a result of misleading title where creators would use ambiguous thumbnails to gain clicks but result in negative feedback from viewers")
    country_mapping = {
    'AF': 'AFG', 'AX': 'ALA',
    'AL': 'ALB', 'DZ': 'DZA',
    'AS': 'ASM', 'AD': 'AND',
    'AO': 'AGO', 'AI': 'AIA',
    'AQ': 'ATA', 'AG': 'ATG',
    'AR': 'ARG', 'AM': 'ARM',
    'AW': 'ABW', 'AU': 'AUS',
    'AT': 'AUT', 'AZ': 'AZE',
    'BS': 'BHS', 'BH': 'BHR',
    'BD': 'BGD', 'BB': 'BRB',
    'BY': 'BLR', 'BE': 'BEL',
    'BZ': 'BLZ', 'BJ': 'BEN',
    'BM': 'BMU', 'BT': 'BTN',
    'BO': 'BOL', 'BQ': 'BES',
    'BA': 'BIH', 'BW': 'BWA',
    'BV': 'BVT', 'BR': 'BRA',
    'IO': 'IOT', 'BN': 'BRN',
    'BG': 'BGR', 'BF': 'BFA',
    'BI': 'BDI', 'CV': 'CPV',
    'KH': 'KHM', 'CM': 'CMR',
    'CA': 'CAN', 'KY': 'CYM',
    'CF': 'CAF', 'TD': 'TCD',
    'CL': 'CHL', 'CN': 'CHN',
    'CX': 'CXR', 'CC': 'CCK',
    'CO': 'COL', 'KM': 'COM',
    'CG': 'COG', 'CD': 'COD',
    'CK': 'COK', 'CR': 'CRI',
    'CI': 'CIV', 'HR': 'HRV',
    'CU': 'CUB', 'CW': 'CUW',
    'CY': 'CYP', 'CZ': 'CZE',
    'DK': 'DNK', 'DJ': 'DJI',
    'DM': 'DMA', 'DO': 'DOM',
    'EC': 'ECU', 'EG': 'EGY',
    'SV': 'SLV', 'GQ': 'GNQ',
    'ER': 'ERI', 'EE': 'EST', 
    'SZ': 'SWZ', 'ET': 'ETH',
    'FK': 'FLK', 'FO': 'FRO',
    'FJ': 'FJI',
    'FI': 'FIN',
    'FR': 'FRA',
    'GF': 'GUF',
    'PF': 'PYF',
    'TF': 'ATF',
    'GA': 'GAB',
    'GM': 'GMB',
    'GE': 'GEO',
    'DE': 'DEU',
    'GH': 'GHA',
    'GI': 'GIB',
    'GR': 'GRC',
    'GL': 'GRL',
    'GD': 'GRD',
    'GP': 'GLP',
    'GU': 'GUM',
    'GT': 'GTM',
    'GG': 'GGY',
    'GN': 'GIN',
    'GW': 'GNB',
    'GY': 'GUY',
    'HT': 'HTI',
    'HM': 'HMD',
    'VA': 'VAT',
    'HN': 'HND',
    'HK': 'HKG',
    'HU': 'HUN',
    'IS': 'ISL',
    'IN': 'IND',
    'ID': 'IDN',
    'IR': 'IRN',
    'IQ': 'IRQ',
    'IE': 'IRL',
    'IM': 'IMN',
    'IL': 'ISR',
    'IT': 'ITA',
    'JM': 'JAM',
    'JP': 'JPN',
    'JE': 'JEY',
    'JO': 'JOR',
    'KZ': 'KAZ',
    'KE': 'KEN',
    'KI': 'KIR',
    'KP': 'PRK',
    'KR': 'KOR',
    'KW': 'KWT',
    'KG': 'KGZ',
    'LA': 'LAO',
    'LV': 'LVA',
    'LB': 'LBN',
    'LS': 'LSO',
    'LR': 'LBR',
    'LY': 'LBY',
    'LI': 'LIE',
    'LT': 'LTU',
    'LU': 'LUX',
    'MO': 'MAC',
    'MK': 'MKD',
    'MG': 'MDG',
    'MW': 'MWI',
    'MY': 'MYS',
    'MV': 'MDV',
    'ML': 'MLI',
    'MT': 'MLT',
    'MH': 'MHL',
    'MQ': 'MTQ',
    'MR': 'MRT',
    'MU': 'MUS',
    'YT': 'MYT',
    'MX': 'MEX',
    'FM': 'FSM',
    'MD': 'MDA',
    'MC': 'MCO',
    'MN': 'MNG',
    'ME': 'MNE',
    'MS': 'MSR',
    'MA': 'MAR',
    'MZ': 'MOZ',
    'MM': 'MMR',
    'NA': 'NAM',
    'NR': 'NRU',
    'NP': 'NPL',
    'NL': 'NLD',
    'NC': 'NCL',
    'NZ': 'NZL',
    'NI': 'NIC',
    'NE': 'NER',
    'NG': 'NGA',
    'NU': 'NIU',
    'NF': 'NFK',
    'MP': 'MNP',
    'NO': 'NOR',
    'OM': 'OMN',
    'PK': 'PAK',
    'PW': 'PLW',
    'PS': 'PSE',
    'PA': 'PAN',
    'PG': 'PNG',
    'PY': 'PRY',
    'PE': 'PER',
    'PH': 'PHL',
    'PN': 'PCN',
    'PL': 'POL',
    'PT': 'PRT',
    'PR': 'PRI',
    'QA': 'QAT',
    'RE': 'REU',
    'RO': 'ROU',
    'RU': 'RUS',
    'RW': 'RWA',
    'BL': 'BLM',
    'SH': 'SHN',
    'KN': 'KNA',
    'LC': 'LCA',
    'MF': 'MAF',
    'PM': 'SPM',
    'VC': 'VCT',
    'WS': 'WSM',
    'SM': 'SMR',
    'ST': 'STP',
    'SA': 'SAU',
    'SN': 'SEN',
    'RS': 'SRB',
    'SC': 'SYC',
    'SL': 'SLE',
    'SG': 'SGP',
    'SX': 'SXM',
    'SK': 'SVK',
    'SI': 'SVN',
    'SB': 'SLB',
    'SO': 'SOM',
    'ZA': 'ZAF',
    'GS': 'SGS',
    'SS': 'SSD',
    'ES': 'ESP',
    'LK': 'LKA',
    'SD': 'SDN',
    'SR': 'SUR',
    'SJ': 'SJM',
    'SE': 'SWE',
    'CH': 'CHE',
    'SY': 'SYR',
    'TW': 'TWN',
    'TJ': 'TJK',
    'TZ': 'TZA',
    'TH': 'THA',
    'TL': 'TLS',
    'TG': 'TGO',
    'TK': 'TKL',
    'TO': 'TON',
    'TT': 'TTO',
    'TN': 'TUN',
    'TR': 'TUR',
    'TM': 'TKM',
    'TC': 'TCA',
    'TV': 'TUV',
    'UG': 'UGA',
    'UA': 'UKR',
    'AE': 'ARE',
    'GB': 'GBR',
    'UM': 'UMI',
    'US': 'USA',
    'UY': 'URY',
    'UZ': 'UZB',
    'VU': 'VUT',
    'VE': 'VEN',
    'VN': 'VNM',
    'VG': 'VGB',
    'VI': 'VIR',
    'WF': 'WLF',
    'EH': 'ESH',
    'YE': 'YEM',
    'ZM': 'ZMB',
    'ZW': 'ZWE',
    'VN': 'VNM',
}
    df_agg_sub['Country Code 3'] = df_agg_sub['Country Code'].map(country_mapping)
    df_views_by_country = df_agg_sub.groupby('Country Code 3')['Views'].sum().reset_index()
    
    fig = px.choropleth(
        df_views_by_country,
        locations='Country Code 3',
        color='Views',
        color_continuous_scale='Blues',
        color_continuous_midpoint=df_views_by_country['Views'].median(),
        title='Total Views by Country',
        projection='natural earth'  # Try different projections here
    )
    
    # Set the layout for the map
    fig.update_geos(
        showcountries=True,
        countrycolor="gray",
        showocean=True,
        oceancolor="lightblue",
        showland=True,
        landcolor="white",
        showcoastlines=True,
        coastlinecolor="darkgray",
        showframe=False
    )
    fig.update_layout(height=500, margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig.update_traces(marker_line_color='black', 
                  marker_line_width=0.5)
    
    st.info('Subscribers by Countries')
    st.plotly_chart(fig)
    
    excluded_countries = ['USA', 'IND']

    # Filter the DataFrame to exclude specific countries
    df_filtered = df_views_by_country[~df_views_by_country['Country Code 3'].isin(excluded_countries)]
    fig = px.choropleth(
        df_filtered,
        locations='Country Code 3',
        color='Views',
        color_continuous_scale='Blues',
        color_continuous_midpoint=df_views_by_country['Views'].median(),
        title='Total Views by Country',
        projection='natural earth'  # Try different projections here
    )
    
    # Set the layout for the map
    fig.update_geos(
        showcountries=True,
        countrycolor="gray",
        showocean=True,
        oceancolor="lightblue",
        showland=True,
        landcolor="white",
        showcoastlines=True,
        coastlinecolor="darkgray",
        showframe=False
    )
    fig.update_layout(height=500, margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig.update_traces(marker_line_color='black', 
                  marker_line_width=0.5)
    
    st.info("Subscribers by Countries (Except USA, IND')") 
    st.plotly_chart(fig)
