import filecmp
import oci, logging
from oci.object_storage.models import CreateBucketDetails
from oci.signer import Signer
import datetime as DT

import send_mail

# Enable debug logging
logging.getLogger('oci').setLevel(logging.DEBUG)
#oci.base_client.is_http_log_enabled(True)

def put_object_to_storage(bucket_name, object_name, data_to_write):
    try:
        config = oci.config.from_file()
        compartment_id = config["tenancy"]
        object_storage = oci.object_storage.ObjectStorageClient(config)

        namespace = object_storage.get_namespace().data
        print('SUCCESS: Got config details')
        #print(config, compartment_id, object_storage, namespace, BUCKET_NAME)
        #print('-------')

        # Retrieve the file, streaming it into another file in 1 MiB chunks
        
        print('Storing status file to object storage--------')
        
        obj = object_storage.put_object(
            namespace,
            bucket_name,
            object_name,
            data_to_write)
    except Exception as e:
        print('ERROR: Saving results data to Object Storage.\n' + str(e))
        return False, str(e)

    print('SUCCESS: Saving results data to Object Storage successful')
    return True, "Success"

if __name__ == '__main__':
    BUCKET_NAME = "Bucket-for-crop-health-project"
    OBJECT_TO_RETRIEVE = 'check_health_status_obj'+DT.date.today()+'.txt'
    data_to_write = "_nothing_"
    status, e = put_object_to_storage(BUCKET_NAME, OBJECT_TO_RETRIEVE, data_to_write)
    if status == False:
        print('UNABLE TO SAVE RESULTS OBJECT...could not save results data to Object Storage')
        send_mail.write_to_file('ERROR-OBJ_STORE_SAVE', e)
    else:
        print(status, e)
        



