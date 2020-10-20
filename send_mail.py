#
# oci-email-send-python version 1.0.
#
# Copyright (c) 2020 Oracle, Inc.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#

import io, os, json, smtplib, email.utils, random, glob
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders 
import datetime as DT
from cryptography.fernet import Fernet 


def write_to_file(prefix, content):
    n = str(random.random())
    today_date = str(DT.date.today())
    #print(">>>> " + n)
    #print(">>>> " + today_date)
    f = open(prefix + "_" + today_date + "_" + n + ".txt", "a")
    f.write(today_date + ": " + content)
    f.close()

def send_email(mail_contents, unique_mail_farm_dict):
    try:
        smtp_username, smtp_password = get_cred()
    except Exception as ex:
        print("ERROR in getting SMTP details: ", ex, flush=True)
        write_to_file("ERROR-SMTP", "ERROR in getting SMTP details: " + str(ex))
        return False

    smtp_host = "smtp.us-ashburn-1.oraclecloud.com"
    smtp_port = 587
    sender_email = "Connect@DeepVisionTech.AI"
    sender_name = "Crop Health (DeepVisionTech.AI)"
    recipient = subject = body = ""
    STATUS = []

    for mail_con in mail_contents:
        success_flag1 = success_flag2 = success_flag3 = True
        #recipient = mail_con['recipient']
        recipient = mail_con
        farms_list = unique_mail_farm_dict.get(mail_con)

        try:
            fromDate = DT.date.today()
            toDate = fromDate - DT.timedelta(days=7)
            subject = "Crop Health for the week " + str(toDate) + " to " + str(fromDate)
            body = "Hello there, <br><br>We hope you are doing well.<br>This email is regarding your weekly Crop Health for the week " \
                            + str(toDate) + " to " + str(fromDate) + "."
            
            #print("subject: " + subject) 
            #print("Body: " + body) 
        except Exception as ex:
            print("ERROR in generating email headers: ", ex, flush=True)
            #raise
            success_flag1 = False
            STATUS.append({recipient: "FAILED"})
            continue

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = email.utils.formataddr((sender_name, sender_email))
            msg['To'] = recipient

            #filename = recipient + ".png"
            files_for_email = glob.glob(recipient + '*.png')
            print(">>> Got "+str(len(files_for_email))+" image files for email " + recipient)
            cnt = 0
            if len(files_for_email) > 0:
                farms_list_copy = farms_list.copy()
                for img_file in files_for_email:
                    ffile = os.path.basename(img_file)
                    print("FILE: " + ffile)
                    frm_in_ffile = ffile[ffile.find('_')+1 : ffile.find('.png')]
                    print("Farm name in file: " + frm_in_ffile)
                    
                    if frm_in_ffile in farms_list_copy:
                        #print(">>>>>>>> attachment for this farm is available" + frm_in_ffile)

                        attachment = open("./" + os.path.basename(img_file), "rb") 
                    
                        p = MIMEBase('application', 'octet-stream') 
                        p.set_payload((attachment).read()) 
                        encoders.encode_base64(p) 
                        p.add_header('Content-Disposition', "attachment; filename=" + os.path.basename(img_file)) 
                        msg.attach(p) 
                        farms_list_copy.remove(frm_in_ffile)

                    #else:
                        #print(">>>>>>>> NO attachment for this farm is available" + frm_in_ffile)
                    
                    
                    cnt = cnt + 1

                body =  body + "<br><br>Attached graph(s) show health status of all the monitored farms for current and previous 2 months." 
                
                print(len(farms_list_copy))
                if len(farms_list_copy) > 0:
                    body =  body + "<br>NOTE: Satellite images for few farms are unavailable or unusable. So, health graphs are not attached for these farms: "
                    fff = ""
                    for kk in farms_list_copy:
                        print("## one or more farms did not have images...adding their name: " + str(kk))
                        fff = fff + str(kk) + ", "
                    body = body + fff

            else:
                print("No images for this email...so, not attaching anything.")
                body = body + '<br><br>NOTE: Satellite images are unavailable or unusable. So, we are unable to show health graph.'

            print("len(farms_list): " + str(len(farms_list)))
            body = getBodyContent(body, mail_con, farms_list)
            #print('after calling getBodyContent(): ' + body)

            msg.attach(MIMEText(body, 'html'))

        except Exception as ex:
            print("ERROR in attaching images to email: ", ex, flush=True)
            #raise
            success_flag2 = False
            if success_flag1 == True:
                STATUS.append({recipient: "FAILED"})
            continue

        try: 
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, recipient, msg.as_string())
            server.close()
        except Exception as ex:
            print("ERROR in sending email: ", ex, flush=True)
            #raise
            success_flag3 = False
            if (success_flag1 == True) and (success_flag2 == True):
                STATUS.append({recipient: "FAILED"})
            continue
        else:
            print ("INFO: Email successfully sent!", flush=True)

        STATUS.append({recipient: "SUCCESS"})

    return STATUS

def getBodyContent(body, mail, farms_list): 

    URL_TO_INVOKE_FN = "https://ackamrxc4anoos3auilnhwzt2q.apigateway.us-ashburn-1.oci.customer-oci.com/delsub/delsub"
    body = body + "<br>NOTE: In case Satellite images for any farm is unavailable or unusable, our system \'predicts\' the health of farm using previous 8 months\' health data. " \
                    + "<br>Health anomalies are categorized as below: " \
                    + "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;1. 'mild' - variation upto Sensitivity lower threshold chosen for the farm" \
                    + "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;2. 'medium' - variation upto 10% of Sensitivity lower threshold chosen for the farm" \ 
                    + "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;3. 'severe' - variation beyond 10% of Sensitivity lower threshold chosen for the farm" \
                    + "<br>Thanks & Regards,<br>Team <a href='https://DeepVisionTech.AI'>DeepVisionTech Pvt. Ltd.</a>" \
                    + "<br><br>Click here to unsubscribe from email notifications: " \
                    + "<a href='"+URL_TO_INVOKE_FN+"?mail="+mail+"&farm=all'>All farms</a>"
                    
    links = ""
    for frm in farms_list:
        link = URL_TO_INVOKE_FN + "?mail="+mail+"&farm="+frm
        links = links + " | <a href='"+link+"'>"+frm+"</a>"

    body = body + links

    return body

def get_cred():
    cred_filename = 'CredFile.ini'
    key_file = 'key.key'

    key = '' 

    with open('key.key','r') as key_in: 
        key = key_in.read().encode() 

    #If you want the Cred file to be of one 
    # time use uncomment the below line 
    #os.remove(key_file) 

    f = Fernet(key) 
    with open(cred_filename,'r') as cred_in: 
        lines = cred_in.readlines() 
        config = {} 
        for line in lines: 
            tuples = line.rstrip('\n').split('=',1) 
            if tuples[0] in ('Username','Password'): 
                config[tuples[0]] = tuples[1] 

        username = (config['Username'])
        passwd = f.decrypt(config['Password'].encode()).decode() 
        #print("Username:", username)
        #print("Password:", passwd) 

    return username, passwd


if __name__ == '__main__':
    mail_contents = ["jay.test.test1@gmail.com"] # NOTE: update with email ids to test
    status = send_email(mail_contents)
    if status == False:
        print('UNABLE TO SEND EMAILs...could not retrieve SMTP server details')
        write_to_file('ERROR-EMAIL', 'UNABLE TO SEND EMAILs...could not retrieve SMTP server details')
    else:
        print(status)
        write_to_file('STATUS-EMAIL', str(status))