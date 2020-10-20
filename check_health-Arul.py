import os, glob
import ee
import geemap
import ipywidgets as widgets
from IPython.display import display
from IPython.display import clear_output
from json import loads 
import numpy as np
import tensorflow as tf
import pandas as pd
pd.options.mode.chained_assignment = None
import plotly.express as px
import plotly.graph_objects as go
import warnings
import random
import datetime
import dateutil.relativedelta
warnings.filterwarnings('ignore')
from tensorflow.python.util import deprecation
from email_validator import validate_email, EmailNotValidError

import send_mail
import retrieve_obj
import save_obj

deprecation._PRINT_DEPRECATION_WARNINGS = False

np.random.seed(1)

# Retrieve the Object (csv file) containing list of emails from OCI Object storage
OBJECT_TO_RETRIEVE = 'check_health_file_obj.csv'
BUCKET_NAME = "Bucket-for-crop-health-project"
status, filename_or_error = retrieve_obj.retrieve_object(BUCKET_NAME, OBJECT_TO_RETRIEVE)
if status == False:
    print('UNABLE TO RETRIEVE OBJECT...could not retrieve date from Object Storage')
    send_mail.write_to_file('ERROR-OBJ_STORE_RETRV', filename_or_error)
    raise Exception(filename_or_error)
else:
    print(status, filename_or_error)

df1 = pd.read_csv(filename_or_error)
location = list(df1['location'])
mail = list(df1['mail id'])
farm_name = list(df1['farm_name'])
threshold = list(df1['threshold'])
Map = geemap.Map()

r1 = {"January":{"NDVI":{"min":0.61,"max":0.75},"EVI":{"min":1.233,"max":1.550}},
      "February":{"NDVI":{"min":0.71,"max":0.85},"EVI":{"min":1.460,"max":1.777}},
      "March":{"NDVI":{"min":0.725,"max":0.835},"EVI":{"min":1.494,"max":1.743}},
      "April":{"NDVI":{"min":0.295,"max":0.415},"EVI":{"min":0.519,"max":0.791}},
      "May":{"NDVI":{"min":0.101,"max":0.151},"EVI":{"min":0.079,"max":0.192}},
      "June":{"NDVI":{"min":0.155,"max":0.215},"EVI":{"min":0.201,"max":0.337}},
      "July":{"NDVI":{"min":0.3,"max":0.325},"EVI":{"min":0.530,"max":0.587}},
      "August":{"NDVI":{"min":0.595,"max":0.715},"EVI":{"min":1.199,"max":1.471}},
      "September":{"NDVI":{"min":0.565,"max":0.72},"EVI":{"min":1.131,"max":1.482}},
      "October":{"NDVI":{"min":0.41,"max":0.55},"EVI":{"min":0.780,"max":1.097}},
      "November":{"NDVI":{"min":0.101,"max":0.215},"EVI":{"min":0.079,"max":0.337}},
      "December":{"NDVI":{"min":0.315,"max":0.487},"EVI":{"min":0.564,"max":0.954}}}

r2 = {"January":{"NDVI":{"min":0.585,"max":0.708},"EVI":{"min":1.176,"max":1.455}},
      "February":{"NDVI":{"min":0.685,"max":0.831},"EVI":{"min":1.403,"max":1.734}},
      "March":{"NDVI":{"min":0.699,"max":0.825},"EVI":{"min":1.435,"max":1.720}},
      "April":{"NDVI":{"min":0.285,"max":0.405},"EVI":{"min":0.496,"max":1.768}},
      "May":{"NDVI":{"min":0.094,"max":0.145},"EVI":{"min":0.063,"max":0.179}},
      "June":{"NDVI":{"min":0.145,"max":0.21},"EVI":{"min":0.0179,"max":0.326}},
      "July":{"NDVI":{"min":0.285,"max":0.362},"EVI":{"min":0.496,"max":0.671}},
      "August":{"NDVI":{"min":0.585,"max":0.705},"EVI":{"min":1.176,"max":1.448}},
      "September":{"NDVI":{"min":0.555,"max":0.715},"EVI":{"min":1.108,"max":1.471}},
      "October":{"NDVI":{"min":0.401,"max":0.503},"EVI":{"min":0.759,"max":0.990}},
      "November":{"NDVI":{"min":0.121,"max":0.259},"EVI":{"min":0.124,"max":0.437}},
      "December":{"NDVI":{"min":0.32,"max":0.475},"EVI":{"min":0.575,"max":0.927}}}

r3 = {"January":{"NDVI":{"min":0.618,"max":0.746},"EVI":{"min":1.251,"max":1.541}},
      "February":{"NDVI":{"min":0.718,"max":0.845},"EVI":{"min":1.478,"max":1.766}},
      "March":{"NDVI":{"min":0.715,"max":0.827},"EVI":{"min":1.471,"max":1.725}},
      "April":{"NDVI":{"min":0.299,"max":0.42},"EVI":{"min":0.528,"max":0.802}},
      "May":{"NDVI":{"min":0.102,"max":0.155},"EVI":{"min":0.081,"max":0.201}},
      "June":{"NDVI":{"min":0.149,"max":0.22},"EVI":{"min":0.188,"max":0.349}},
      "July":{"NDVI":{"min":0.31,"max":0.321},"EVI":{"min":0.553,"max":0.578}},
      "August":{"NDVI":{"min":0.601,"max":0.719},"EVI":{"min":1.213,"max":1.480}},
      "September":{"NDVI":{"min":0.559,"max":0.729},"EVI":{"min":1.117,"max":1.503}},
      "October":{"NDVI":{"min":0.415,"max":0.562},"EVI":{"min":0.791,"max":1.124}},
      "November":{"NDVI":{"min":0.111,"max":0.249},"EVI":{"min":0.102,"max":0.415}},
      "December":{"NDVI":{"min":0.331,"max":0.495},"EVI":{"min":0.600,"max":0.972}}}

model = tf.keras.models.load_model('anamoly_sen.h5')

def regionReduce(img, props):
  date = img[props[0]]
  
  
  stat = img[props[1]].reduceRegion(
    reducer = reReArgs['reducer'],
    geometry = reReArgs['geometry'],
    scale = reReArgs['scale'])

  return(ee.Feature(None, stat).copyProperties(img[props[1]], img[props[1]].propertyNames()).set({'Date': date}))

def getReReList(col, props):
    d = []
    for i in col:
        r = regionReduce(i,props)
        d.append(r)
    da = ee.FeatureCollection(d)
    dict = {}
    dict =  da.filter(ee.Filter.notNull(props)).reduceColumns(reducer = ee.Reducer.toList().repeat(len(props)),selectors = props)

    return (ee.List(dict.get('list')).getInfo())

def create_seq(X,y,time_steps=1):
    Xs,ys=[],[]
    for i in range(len(X)-time_steps):
        Xs.append(X.iloc[i:(i+time_steps)].values)
        ys.append(y.iloc[i+time_steps])
    return np.array(Xs), np.array(ys)

def chkim(aug):
    ln = len(aug)
    x = aug.count(True)
    pr = (0.40 * ln)
    if (x == ln):
        return("100p")
    elif (x >= int(round(pr))):
        return("40p")
    else:
        return("l40p")

def fill_values(df):
    x = random.choice([r1,r2,r3])
    aug = []
    for i in range(len(df.index)):
      if pd.isna(df.at[i,'EVI']):
        date = df.at[i,'date']
        month = date.strftime("%B")
        df.at[i,'EVI'] = random.uniform(x[month]['EVI']['min'],x[month]['EVI']['max'])
      if pd.isna(df.at[i,'NDVI']):
        date = df.at[i,'date']
        month = date.strftime("%B")
        df.at[i,'NDVI'] = random.uniform(x[month]['NDVI']['min'],x[month]['NDVI']['max'])
        aug.append(True)
      else:
        aug.append(False)
    df['aug'] = aug
    st = chkim(aug)
    return df,st

def create_df(NDVI,EVI):
    NDVI = pd.DataFrame(NDVI)
    NDVI = NDVI.transpose()
    NDVI.columns = ['Date', 'NDVI']
    NDVI['Date'] = pd.to_datetime(NDVI['Date'])
    NDVI = NDVI.set_index('Date')
    EVI = pd.DataFrame(EVI)
    EVI = EVI.transpose()
    EVI.columns = ['Date', 'EVI']
    EVI['Date'] = pd.to_datetime(EVI['Date'])
    EVI = EVI.set_index('Date')
    df = pd.concat([NDVI,EVI],axis=1)
    dates = pd.date_range(start=(from_date),end=(to_date),freq='MS')
    df = df.reindex(dates)
    df = df.infer_objects()
    df = df.reset_index()
    df = df.rename(columns={"index":"date"})
    df,st = fill_values(df)
    if (st == "40p"):
        df2 = pd.DataFrame(df[8:])
        df3 = df2[df2.aug==False]
        return df3,st
    else:
        return df,st

def predict(df,threshold):
    X,y = create_seq(df[['NDVI','EVI']],df.NDVI,8)
    X_pred= model.predict(X)
    mae_loss = np.abs(X_pred[:,0] - y)
    
    ndvi_thresholdn = threshold
    ndvi_thresholdl = (threshold+0.1)
    ndvi_thresholdu = (threshold+0.2)
    
    score_df = pd.DataFrame(df[8:])

    score_df['loss_NDVI'] = mae_loss
    
    score_df['threshold_NDVIn'] = ndvi_thresholdn
    
    score_df['threshold_NDVIl'] = ndvi_thresholdl
    
    score_df['threshold_NDVIu'] = ndvi_thresholdu
    
    score_df['anomaly_NDVIn'] = ((score_df.loss_NDVI > score_df.threshold_NDVIn) & (score_df.loss_NDVI < score_df.threshold_NDVIl) & (score_df.loss_NDVI < score_df.threshold_NDVIu))

    score_df['anomaly_NDVIl'] = ((score_df.loss_NDVI > score_df.threshold_NDVIl) & (score_df.loss_NDVI < score_df.threshold_NDVIu))
    
    score_df['anomaly_NDVIu'] = score_df.loss_NDVI > score_df.threshold_NDVIu
    
    score_df['NDVI'] = df[8:].NDVI
    
    score_df['prediction'] = X_pred[:,0]
    score_df['date'].iloc[-1]= to_date
    if (score_df.aug.values[-1]==True):
        score_df['anomaly_NDVIn'].iloc[-1] = False
        score_df['anomaly_NDVIl'].iloc[-1] = False
        score_df['anomaly_NDVIu'].iloc[-1] = False
        score_df['NDVI'].iloc[-1] = score_df['prediction'].iloc[-1]
    
    anomalies_NDVIn = score_df[score_df.anomaly_NDVIn == True]
    
    anomalies_NDVIl = score_df[score_df.anomaly_NDVIl == True]
    
    anomalies_NDVIu = score_df[score_df.anomaly_NDVIu == True]
    
    anomalies_NDVIa = score_df[score_df.aug == True]
    print(">>> DOne with prediction....returning")
    
    return anomalies_NDVIl,anomalies_NDVIu,anomalies_NDVIn,anomalies_NDVIa,score_df

def aplot(andvil,andviu,andvin,andvia,sdf,farm,name):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sdf.date, y=sdf.NDVI,mode='lines+markers',name='Health Graph',line = dict(color="#00fc41",width=4),marker = dict(color = 'rgb(0, 252, 65)',size = 15)))
    fig.add_trace(go.Scatter(x=andvin.date, y=andvin.NDVI,mode='markers',name='Mild anomaly',marker = dict(color = 'rgb(253, 229, 52)',size = 15)))
    fig.add_trace(go.Scatter(x=andvil.date, y=andvil.NDVI,mode='markers',name='Medium anomaly',marker = dict(color = 'rgb(235, 153, 52)',size = 15)))
    fig.add_trace(go.Scatter(x=andviu.date, y=andviu.NDVI,mode='markers',name='Severe anomaly',marker = dict(color = 'rgb(235, 52, 52)',size = 15)))
    fig.add_trace(go.Scatter(x=andvia.date, y=andvia.NDVI,mode='markers',name='Predicted data',marker = dict(color = 'rgb(0, 0, 0)',size = 10)))
    fig.update_layout(title="Health Graph for "+farm,showlegend=True,font=dict(family="Courier New, monospace",size=18,color="RebeccaPurple"))
    fig.write_image(name+".png")
    print(">>> image file saved..." + name+'.png')
    return

def bplot(df,name,nme):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.date, y=df.NDVI,mode='markers',name='Halth value',marker = dict(color = 'rgb(0, 0, 0)',size = 15)))
    fig.update_layout(title="Health Graph for "+nme+" (Not assessed for abnormalities)",showlegend=True,font=dict(family="Courier New, monospace",size=18,color="RebeccaPurple"))
    fig.write_image(name+".png")
    return

def maskS2clouds(image):
    qa = image.select('QA60')
    cloudBitMask = 1 << 10
    cirrusBitMask = 1 << 11
    mask = qa.bitwiseAnd(cloudBitMask).eq(0).And(qa.bitwiseAnd(cirrusBitMask).eq(0))

    return image.updateMask(mask).divide(10000)

def EVI(image):
    return image.expression(
        '(2.5*(NIR-R))/(NIR+(2.4*R)+1)', 
        {
        'NIR': image.select('B8'),
        'R': image.select('B4')
        })

def ProcessImg(region,from_date,to_date,clouds_percentage):
    
    NUM_OF_MONTHS = ee.Date(to_date).difference(from_date, 'month')
    
    region_to_clip = ee.FeatureCollection(region)

    NUM_OF_MONTHS_TO_DISPLAY = NUM_OF_MONTHS.round()

    Filtered_Collection = Sentinal_dataset.filterBounds(region_to_clip)

    filteredRegion_Date_month_to_display = Filtered_Collection.filterDate(from_date, to_date)
    
    GLOBAL_NDVI = []
    GLOBAL_EVI = []
    delta = 0
    j = 0
    for i in range(NUM_OF_MONTHS_TO_DISPLAY.getInfo()):
        from_date_next = ee.Date(from_date).advance(delta, 'month')
        to_date_next = from_date_next.advance(30, 'day')
        filteredRegion_Date_month = Filtered_Collection.filterDate(from_date_next, to_date_next)
        filteredRegion_Date_month_unmastCloud = filteredRegion_Date_month.map(maskS2clouds)

        numImg = filteredRegion_Date_month_unmastCloud.size().getInfo()

        if(numImg < 1):
            delta+=1
            continue
        
        medianRGB = filteredRegion_Date_month_unmastCloud.median()
        medianNDVI = medianRGB.normalizedDifference(['B8','B4'])
        NDVI_VALUE_DICT = {"Date": from_date_next.format('dd MMM YYYY').getInfo(), "NDVI": ee.Image(medianNDVI).select([0], ['NDVI'])}
        GLOBAL_NDVI.append(NDVI_VALUE_DICT)

        medianEV = filteredRegion_Date_month_unmastCloud.map(EVI)
        medianEVI = medianEV.median()
        EVI_VALUE_DICT = {"Date": from_date_next.format('dd MMM YYYY').getInfo(), "EVI": ee.Image(medianEVI).select([0], ['EVI'])}
        GLOBAL_EVI.append(EVI_VALUE_DICT)

        delta+=1
        j+=1
        
    return GLOBAL_NDVI,GLOBAL_EVI

def delete_image_files():
    image_files = glob.glob('*.png')
    print(">>> Got "+str(len(image_files)))
    for img_file in image_files:
        print("Deleting..." + img_file)
        os.remove(img_file)

def can_send_notification(num_days):
    success_files = glob.glob('SUCCESS-EMAIL*.txt')
    success_files.sort(key=os.path.getmtime)
    print("\n".join(success_files))
    print(">>> Got "+str(len(success_files))+" SUCCESS files in folder...")

    if len(success_files) == 0:
        print("No files found. So, NOT notified in the last "+str(num_days)+" days")
        return True

    suc_file = success_files[len(success_files)-1]
    print(">>>>> latest file: " + suc_file)
    
    name = os.path.basename(suc_file)
    first_underscore = name.find('_') 
    if first_underscore > 0:
        second_underscore = name.find('_', first_underscore+1) 
        date_in_name = name[first_underscore+1 : second_underscore]
        print('Date in filename: ' + date_in_name)
        date_notified = datetime.datetime.strptime(date_in_name, '%Y-%m-%d')
        date_notified = date_notified.date()
        #print(date_notified)
        today_date = datetime.date.today()
        date_diff = today_date - datetime.timedelta(days=num_days)
        print("Need to check till Date: " + str(date_diff))
        if date_notified > date_diff:
            print("notified in the last "+str(num_days)+" days")
            return False
        else:
            print("NOT notified in the last "+str(num_days)+" days")
            return True

    # True - notification was NOT sent in the last 'num_days'
    # False - notification was sent in the last 'num_day'


if __name__ == '__main__':
    # Check if the notifications were sent in the past 6 days. if not, then run this script. else don't run
    NUM_OF_DAYS_TO_CHECK = 7
    status = can_send_notification(NUM_OF_DAYS_TO_CHECK)

    if status == False:
        print("**************************************************")
        print("Already notified in the past "+str(NUM_OF_DAYS_TO_CHECK)+" days. So CANNOT notify now")
        print("**************************************************")
        print("NOTE: ")
        print("If you need to notify forcefully, edit the NUM_OF_DAYS_TO_CHECK in this script to a value 100 and rerun this script")
        print("********************************************************************************************************************")
        
    else:
        print("NOT notified in the past "+str(NUM_OF_DAYS_TO_CHECK)+" days. So, can notify now")   

        Sentinal_dataset = ee.ImageCollection("COPERNICUS/S2_SR")

        reReArgs = {
        'reducer': ee.Reducer.mean(),
        'geometry': ee.Geometry.Point([0,0]),
        'scale': 200}

        # NOTE: THIS IS FOR TESTING ONLY. Need to Comment out
        date_input = datetime.datetime.strptime("2019-09-30", '%Y-%m-%d')
        date_input = date_input.date()
        #x = date_input

        x = datetime.datetime.now()
        date = x.strftime("%Y-%m-%d")
        d = datetime.datetime.strptime(date, "%Y-%m-%d")
        d2 = d - dateutil.relativedelta.relativedelta(months=10)
        from_date = d2.strftime("%Y-%m")+"-01"
        to_date = date

        print(from_date)
        print(to_date)
        clouds_percentage = 100
        unique_mail_dict = {}
        unique_mail_farm_dict = {}

        for i in range(len(df1.index)):
            id = mail[i]
            loc = location[i]
            trshld = threshold[i]
            nme = farm_name[i]
            ss = unique_mail_dict.get(id)
            if ss is None:
                ss = 1
                unique_mail_dict.update({id:ss})
            else:
                ss = int(ss) + 1
                unique_mail_dict.update({id:ss})

            frm_nm_list = unique_mail_farm_dict.get(id)
            if (frm_nm_list is None):
                frm_nm_list = []
                frm_nm_list.append(nme)
                unique_mail_farm_dict.update({id:frm_nm_list})
            else:
                frm_nm_list.append(nme)
                unique_mail_farm_dict.update({id:frm_nm_list})
            
            region1 = ee.Geometry.Polygon(loads(loc))

            bigger_region = region1.buffer(0.1)
                    
            reReArgs['geometry'] = region1
            print(">>>>calling ProcessImg()")
            NDVI,EVI1 = ProcessImg(bigger_region,from_date,to_date,clouds_percentage)
            print(">>> returned from ProcessImg")
            ndvi = getReReList(NDVI, ['Date', 'NDVI'])
            evi = getReReList(EVI1, ['Date', 'EVI'])
            df,st = create_df(ndvi,evi)
            if (st == "l40p"):
                print(">>>>>> LESS THAN 40 percent")
                andvil1,andviu1,andvin1,andvia1,sdf1 = predict(df,trshld)
                aplot(andvil1,andviu1,andvin1,andvia1,sdf1, 'Farm ' + str(nme) + "(" + str(ss) + ")", id + '_' + str(nme))
            elif (st == "40p"):
                #bplot(df,id,nme)
                print(">>>>>> EQUAL TO 40 percent")
                andvil1,andviu1,andvin1,andvia1,sdf1 = predict(df,trshld)
                aplot(andvil1,andviu1,andvin1,andvia1,sdf1, 'Farm ' + str(nme) + "(" + str(ss) + ")", id + '_' + str(nme))
            elif (st == "100p"):
                print("No image is available for farm 2")
                continue

        print(unique_mail_dict)
        print(unique_mail_farm_dict)
        unique_mail_list = list(set(mail))
        print("Length of mail: " + str(len(mail)))
        print("Length of unique_mail_list: " + str(len(unique_mail_list)))
        status = send_mail.send_email(unique_mail_list, unique_mail_farm_dict)
        print("results -----------")
        print("deleting the .png files")
        delete_image_files()
        if status == False:
            print('UNABLE TO SEND EMAILs...could not retrieve SMTP server details')
            send_mail.write_to_file('ERROR-EMAIL', 'UNABLE TO SEND EMAILs...could not retrieve SMTP server details')
        else:
            print(status)
            send_mail.write_to_file('SUCCESS-EMAIL', str(status))

            OBJECT_TO_SAVE = 'check_health_status_obj_'+str(datetime.date.today())+'.txt'
            status, filename_or_error = save_obj.put_object_to_storage(BUCKET_NAME, OBJECT_TO_SAVE, str(status))
            if status == False:
                print('UNABLE TO SAVE RESULTS OBJECT...could not save results data to Object Storage')
                send_mail.write_to_file('ERROR-OBJ_STORE_SAVE', filename_or_error)
                raise Exception(filename_or_error)
            else:
                print(status, filename_or_error)