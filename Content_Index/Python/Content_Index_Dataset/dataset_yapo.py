#Librerias
#%load_ext autoreload
#%autoreload 2
import psycopg2
import numpy as np
import pandas as pd
#import matplotlib.pyplot as plt
#%matplotlib inline
import os
#from pandas import DataFrame, read_sql
#import seaborn as sns
#sns.set_style("whitegrid")
#from pandas import DataFrame, to_datetime
#from IPython.display import display
path = os.path.expanduser('~')
#import datetime as dt
import pandas.io.sql as psql

df = ''

# Function to compute extremal values and quartiles
def q010(x):
    return x.quantile(0.10)

def q1(x):
    return x.quantile(0.25)

def q2(x):
    return x.quantile(0.50)

def q3(x):
    return x.quantile(0.75)

def q090(x):
    return x.quantile(0.90)

f = [q010,q1,q2,q3,q090]

def query_ads():
    conn = ""
    try:
        conn = psycopg2.connect(dbname='dw_blocketdb_ch', user='bnbiuser', host='200.29.173.148',
                                password='VE1bi@BN112AzLkOP')
    except:
        #logger.info('ERROR: I am unable to connect to the database')
            print ("I am unable to connect to the database")

    query = """
    DROP TABLE stg.temp_visits_content;
    CREATE TABLE 
    stg.temp_visits_content as
    select
    x.date_start::date,
    x.list_id::int,
    x.visits::int
    from
    stg.fact_weekly_adview_xiti x
    where
    date_start::date in
    (
    '2018-09-03',
    '2018-09-10',
    '2018-09-17',
    '2018-09-24',
    '2018-10-01',
    '2018-10-08',
    '2018-10-15',
    '2018-10-22',
    '2018-10-29'
    )
    and list_id <> '-';

    select
    a.ad_id_pk,
    a.approval_date::date,
    case when ad_type_id_fk = 1 then 'sell' else 'buy' end as ad_type,
    cm.category_main_id_pk,
    cm.category_main_name,
    a.category_id_fk,
    c.category_name,
    pl.platform_name,
    r.region_name,
    case when sp.seller_id_fk is not null then 'pro' else 'pri' end as pri_pro_seller,
    a.subject,
    a.body,
    a.price,
    case when im.ad_id_nk is null then 'no' else 'yes' end as has_a_photo,
    im.photos,
    im.mean_resol,
    p.params,
    x.visits
    from ods.ad a inner join
    ods.category c on c.category_id_pk = a.category_id_fk
    left join
    ods.category_main cm on cm.category_main_id_pk = c.category_main_id_fk
    left join
    ods.platform pl on pl.platform_id_pk = a.platform_id_fk
    left join
    ods.region r on r.region_id_pk = a.region_id_fk
    left join
    stg.temp_images_per_ad im on im.ad_id_nk = a.ad_id_nk
    left join
    stg.temp_params_content_agg p on p.ad_id = a.ad_id_nk 
    left join
    ods.seller_pro_details sp on sp.seller_id_fk = a.seller_id_fk and sp.category_id_fk = a.category_id_fk
    inner join
    stg.temp_visits_content x on x.date_start::date = a.approval_date::date and x.list_id::int = a.list_id_nk::int
    where a.approval_date::date between '2018-09-01' and '2018-10-31'
    and ad_type_id_fk = 1
    and pl.platform_id_pk in (1,2,5,6,7,8);
    """
    df = psql.read_sql(query, conn)
    conn.close()
    return df

def ad_reply():
    conn = ""
    try:
        conn = psycopg2.connect(dbname='dw_blocketdb_ch', user='bnbiuser', host='200.29.173.148',
                                password='VE1bi@BN112AzLkOP')
    except:
        #logger.info('ERROR: I am unable to connect to the database')
        print("I am unable to connect to the database")

    query = """
    select
    t.ad_id_pk,
    count(t.ad_reply_id_pk) as ad_reply_first_week
    from 
    (
    select 
    a.ad_id_pk,
    r.ad_reply_id_pk,
    case when (r.ad_reply_creation_date::date - a.approval_date::date)::int <= 7 then 1 else 0 end as ad_reply_first_week
    from
    ods.ad_reply r 
    inner join
    ods.ad a on a.ad_id_pk = r.ad_id_fk and a.approval_date::date >= '2018-09-01'
    where
    r.ad_reply_creation_date::date >= '2018-09-01'
    )t
    where 
    ad_reply_first_week = 1
    group by 1
    """
    df_ar = psql.read_sql(query, conn)
    return df_ar

def products():
    conn = ""
    try:
        conn = psycopg2.connect(dbname='dw_blocketdb_ch', user='bnbiuser', host='200.29.173.148',
                                password='VE1bi@BN112AzLkOP')
    except:
        #logger.info('ERROR: I am unable to connect to the database')
        print("I am unable to connect to the database")

    query = """
    select 
    ad_id_fk as ad_id_pk,
    product as product_name
    from
    stg.ad_product
    where 
    approval_date::date >= '2018-09-01'
    and product not like 'None%'
    """
    df_prod = psql.read_sql(query, conn)
    return df_prod

#CATEGORIA EJEMPLO = 30 Y ALGUNOS PARAMETROS PARA COMPLETAR EL DATASET

query_ads()
ad_reply()
products()

df=df[(df.category_id_fk == 30)].copy()
df['len_subject'] = df['subject'].str.split(" ").apply(len)
df['len_body'] = df['body'].str.split(" ").apply(len)
df['len_full_description'] = df['len_subject'] + df['len_body']
#PRECIO
#MUST BE PRICE
df['must_be_price'] = ((df['ad_type'] == 'sell') | (df['ad_type'] == 'buy')).astype(int)
# PRICE MISSING & NORMALIZED
df.loc[(df['must_be_price'] == 1) & (df['price'].isnull()),'price_missing'] = 1
df.loc[(df['must_be_price'] == 1) & (-df['price'].isnull()),'price_missing'] = 0
df['price_log'] = np.log(df.price + 1)
df['price_normalized'] = (df.price-np.min(df.price))/(np.max(df.price)-np.min(df.price))

#PARAMETROS CATEGORY
#ESTA PARTE SE HIZO A MANO EN UN CSV YA QUE SON POCOS PARAMETROS PERO LA FORMA CORRECTA ES HACER UNA AGRUPACION EN BLOCKET
#TAL CUAL COMO ESTA HECHO EN EL EJEMPLO EN GITHUB
params_cat_no_mandatory = pd.read_csv('/Users/Javier/Jupyter/params_per_category_no_mandatory.csv',sep=';')
params_cat_no_mandatory['must_have_params'] = 1
df = df.merge(params_cat_no_mandatory[['category_id_fk', 'total_params_per_category','must_have_params']],how='left',
              on = 'category_id_fk')
df['total_params_per_category'] = df['total_params_per_category'].fillna(0)
df['must_have_params'] = df['must_have_params'].fillna(0)

#Adding information about the quartiles for price, length full_description,
# number of photos, % params per Celulares, telefonos y accesorios

table_len_full_description = df.groupby(['category_name']).agg({'len_full_description':f}).reset_index()
table_price = df[(-df['price'].isnull()) & (df.must_be_price==1)].groupby(['category_name']).agg({'price':f}).reset_index()
table_nof_photos = df.groupby(['category_name']).agg({'photos':f}).reset_index()
table_completness_in_params = df.groupby(['category_name']).agg({'params':f}).reset_index()

#apply percentiles

categories = df.category_name.unique()
huge = 100000000000000000
labels = ['q010','q1','q2','q3','q090', 'q100']
labels_num = [0.10,0.33,0.5,0.66,0.90,1]

def apply_percentiles(cat,table,feature,huge):
    # where we have to change the values
    where_quart = (table['category_name'] == cat)
    where_df = df['category_name'] == cat
    # extracting the values of quartile per this cat and reg
    if np.sum(where_quart) > 0:
        aux = table[where_quart][feature].reset_index()
        table_quartiles = [0,aux['q010'][0]+0.001,aux['q1'][0]+0.002,aux['q2'][0]+0.003,aux['q3'][0]+0.004,aux['q090'][0]+0.005,huge]
        # apply to the new column
        if np.sum(where_df) > 0:
            df.loc[where_df, feature+'_quartil'] = pd.cut(df[where_df][feature],
                                                          bins = table_quartiles,
                                                          labels = labels)
            df.loc[where_df, feature+'_quartil_num'] = pd.cut(df[where_df][feature],
                                                          bins = table_quartiles,
                                                          labels = labels_num)

for cat in categories:
    apply_percentiles(cat,table_completness_in_params,'params',huge)
    apply_percentiles(cat,table_len_full_description,'len_full_description',huge)
    apply_percentiles(cat,table_nof_photos,'photos',huge)
    apply_percentiles(cat,table_price,'price',huge)

table_price.columns = table_price.columns.droplevel() + '_price'
table_price.columns = ['category_name', 'q010_price', 'q1_price', 'q2_price', 'q3_price',
       'q090_price']
table_nof_photos.columns = table_nof_photos.columns.droplevel() + '_nof_photos'
table_nof_photos.columns = ['category_name', 'q010_nof_photos', 'q1_nof_photos',
                            'q2_nof_photos','q3_nof_photos', 'q090_nof_photos']
table_len_full_description.columns = table_len_full_description.columns.droplevel() + '_len_full_description'
table_len_full_description.columns = ['category_name',
       'q010_len_full_description', 'q1_len_full_description',
       'q2_len_full_description', 'q3_len_full_description',
       'q090_len_full_description']
table_completness_in_params.columns = table_completness_in_params.columns.droplevel() + '_completness_in_params'
table_completness_in_params.columns = ['category_name', 'q010_completness_in_params',
       'q1_completness_in_params', 'q2_completness_in_params',
       'q3_completness_in_params', 'q090_completness_in_params']

df  = df.merge(table_price,how='left',on = 'category_name')
df= df.merge(table_nof_photos,how='left',on = 'category_name')
df = df.merge(table_completness_in_params,how='left',on = 'category_name')
df = df.merge(table_len_full_description,how='left',on = 'category_name')
df = df.merge(table_ad_reply,how='left',on = 'ad_id_pk')
df = df.merge(table_prod_name,how='left',on = 'ad_id_pk')

df.to_csv('/Users/Javier/Jupyter/dataset_for_ad_index_phone_accurated_params_no_mandatory.csv', index= False)