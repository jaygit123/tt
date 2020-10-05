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

        try:
            fromDate = DT.date.today()
            toDate = fromDate - DT.timedelta(days=7)
            subject = "Crop Health for the week " + str(toDate) + " to " + str(fromDate)
            body = "Hello there, \n\nWe hope you are doing well.\nThis email is regarding your weekly Crop Health for the week " \
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
            if len(files_for_email) > 0:
                for img_file in files_for_email:
                    print("FILE: " + os.path.basename(img_file))
                    attachment = open("./" + os.path.basename(img_file), "rb") 
                    p = MIMEBase('application', 'octet-stream') 
                    p.set_payload((attachment).read()) 
                    encoders.encode_base64(p) 
                    p.add_header('Content-Disposition', "attachment; filename=" + os.path.basename(img_file)) 
                    msg.attach(p) 

                    body =  body + "\n\nNOTE: The attached graph has health status for current and previous month." 
            else:
                print("No images for this email...so, not attaching anything.")
                body = body + '\n\nNOTE: Satellite images are unavailable or unusable. So, we are unable to show health graph.'

            body = getBodyContent(body, mail_con, unique_mail_farm_dict.get(mail_con))

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

    URL_TO_INVOKE_FN = ""
    body + "\n\nThanks & Regards,\nTeam DeepVisionTech.AI" \
                    + "\n\nVisit us: <a href='https://DeepVisionTech.AI'>DeepVisionTech Pvt. Ltd.</a>" \
                    + "\n\nClick to stop receiving email notification for: " \
                    + "<a href='"+URL_TO_INVOKE_FN+"?email=all&farm_name=all'>All farms</a>"
                    
    for frm in farms_list:
        link = URL_TO_INVOKE_FN + "?email="+mail+"&farm_name="+frm
        body = doby + " | <a href='"+link+"'>"+frm+"</a>"

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