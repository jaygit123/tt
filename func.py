
#
# oci-compute-control-python version 1.0.
#
# Copyright (c) 2020 Oracle, Inc.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
# Fun to start & stop Crop Monitoring VM instance

import io, logging
import json
import oci
from urllib.parse import urlparse, parse_qs

from fdk import response

def instance_status(compute_client, instance_id):
    return compute_client.get_instance(instance_id).data.lifecycle_state

def instance_start(compute_client, instance_id):
    print('Starting Instance: {}'.format(instance_id))
    try:
        if instance_status(compute_client, instance_id) in 'STOPPED':
            try:
                resp = compute_client.instance_action(instance_id, 'START')
                print('Start response code: {0}'.format(resp.status))
            except oci.exceptions.ServiceError as e:
                print('Starting instance failed. {0}' .format(e))
                raise
        else:
            print('The instance was in the incorrect state to start' .format(instance_id))
            raise
    except oci.exceptions.ServiceError as e:
        print('Starting instance failed. {0}'.format(e))
        raise
    print('Started Instance: {}'.format(instance_id))
    return instance_status(compute_client, instance_id)

def instance_stop(compute_client, instance_id):
    print('Stopping Instance: {}'.format(instance_id))
    try:
        if instance_status(compute_client, instance_id) in 'RUNNING':
            try:
                resp = compute_client.instance_action(instance_id, 'STOP')
                print('Stop response code: {0}'.format(resp.status))
            except oci.exceptions.ServiceError as e:
                print('Stopping instance failed. {0}' .format(e))
                raise
        else:
            print('The instance was in the incorrect state to stop' .format(instance_id))
            raise
    except oci.exceptions.ServiceError as e:
        print('Stopping instance failed. {0}'.format(e))
        raise
    print('Stopped Instance: {}'.format(instance_id))
    return instance_status(compute_client, instance_id)

def handler(ctx, data: io.BytesIO=None):

    body = "invalid"
    token = "invalid"
    apiKey = "invalid"
    command = "invalid"

    try:
        # retrieving the request headers
        headers = ctx.Headers()
        logging.getLogger().info("Headers: " + json.dumps(headers))
        token = headers.get("auth_token")
        logging.getLogger().info(">>> got auth_token from header: " + str(token))

        requesturl = ctx.RequestURL()
        logging.getLogger().info("Request URL: " + json.dumps(requesturl))

        parsed_url = urlparse(requesturl)
        query_str = parse_qs(parsed_url.query)
        logging.getLogger().info("Query string: " + json.dumps(query_str))

        body = json.loads(data.getvalue().decode('UTF-8'))
        logging.getLogger().info(">>> got body: " + str(body))
        instance_ocid = body.get("instance_ocid")
        logging.getLogger().info(">>> got instanceocid: " + str(instance_ocid))
        command = body.get("command")
        logging.getLogger().info(">>> got command: " + str(command))        

        app_context = dict(ctx.Config())
        apiKey = app_context['auth_token']

        if token == apiKey:
            logging.getLogger().info('AUTHENTICATION SUCCESSFUL - auth_tokens match!')
        else:
            logging.getLogger().info('AUTHENTICATION FAILED - auth_tokens DO NOT match. Cannot proceed.')
            return response.Response(
                        ctx, 
                        status_code=401, 
                        response_data=json.dumps({"active": False, "wwwAuthenticate": "AUTH_TOKEN"})
                        )

    except (Exception, ValueError) as ex:
        print("Two arguments along with one header need to be passed to the function: instance_ocid, command and auth_token", flush=True)
        logging.getLogger().info('Two arguments along with one header need to be passed to the function: instance_ocid, command and auth_token. \n' + str(ex))
        raise 

    try:
        signer = oci.auth.signers.get_resource_principals_signer()
        compute_client = oci.core.ComputeClient(config={}, signer=signer)

        if command == 'status':
            resp = instance_status(compute_client, instance_ocid)
        elif command == 'start':
            resp = instance_start(compute_client, instance_ocid)
        elif command == 'stop':
            resp = instance_stop(compute_client, instance_ocid)
        else:
            print("Command not supported", flush=True)
            logging.getLogger().info('Command not supported')
            resp = 'command not supported'

        return response.Response(
            ctx, 
            response_data=json.dumps({"status": "{0}".format(resp)}),
            headers={"Content-Type": "application/json"}
        )
    except (Exception, ValueError) as ex:
        print("Command execution failed", flush=True)
        logging.getLogger().info('Command execution failed \n' + str(ex))
        raise 


