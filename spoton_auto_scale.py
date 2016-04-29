import boto3
import logging
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def scale(elb, name, direction, tags, cwapi, ec2api, elbapi):
    request = tags['SpotFleetRequestId']
    scale_min = int(tags.get('SpotFleetRequestScaleMin') or 1)
    scale_max = int(tags.get('SpotFleetRequestScaleMax') or 20)
    alarm = tags.get('SpotFleetRequestScale' + name + 'Alarm')
    steps = int(tags.get('SpotFleetRequestScale' + name + 'Steps') or 1) * direction
    cooldown = int(tags.get('SpotFleetRequestScale' + name + 'Cooldown') or 5) * 60
    last_action = int(tags.get('SpotFleetRequestScale' + name + 'LastAction') or 0)
    
    if alarm:
        
        # check cooldown
        if last_action + cooldown > time.time():
            # scaling still in cooldown!
            logger.info('Skipping %s scaling of SpotFleetRequest %s because it is still on cooldown (on ELB %s)', name, request, elb)
            return True
        
        # check if we need to scale
        alarms_response = cwapi.describe_alarms(AlarmNames=[alarm])
        if not alarms_response['MetricAlarms']:
            logger.error('CloudWatch alarm %s not found for %s scaling SpotFleetRequest %s on ELB %s', alarm, name, request, elb)
            return False
        
        alarm_details = alarms_response['MetricAlarms'][0]
        if alarm_details['StateValue'] != 'ALARM':
            # alarm not in state ALARM
            return False
        
        # scaling necessary!
        
        requests_response = ec2api.describe_spot_fleet_requests(SpotFleetRequestIds=[request])
        if not requests_response['SpotFleetRequestConfigs']:
            logger.error('SpotFleetRequest %s not found on ELB %s', request, elb)
            return False
        
        # get and calculate new target capacity
        request_config = requests_response['SpotFleetRequestConfigs'][0]
        current_target_capacity = request_config['SpotFleetRequestConfig']['TargetCapacity']
        scaled_target_capacity = current_target_capacity + steps
        if scaled_target_capacity < scale_min:
            scaled_target_capacity = scale_min
        if scaled_target_capacity > scale_max:
            scaled_target_capacity = scale_max
        
        if scaled_target_capacity == current_target_capacity:
            logger.info("Skipping %s scaling of SpotFleetRequest %s because target capacity would not be in scaling bounds. Currently: %s <= %s <= %s (on ELB %s)", name, request, scale_min, scaled_target_capacity, scale_max, elb)
            return False
        
        # store new configuration inculding cooldown for next modification
        ec2api.modify_spot_fleet_request(SpotFleetRequestId=request, TargetCapacity=scaled_target_capacity)
        elbapi.add_tags(LoadBalancerNames=[elb], Tags=[{'Key': 'SpotFleetRequestScale' + name + 'LastAction', 'Value': '{}'.format(int(time.time()))}])
        
        logger.info('Scaled %s SpotFleetRequest %s by %s instances to a new target capacity of %s instances (for ELB %s)', name, request, (scaled_target_capacity - current_target_capacity), scaled_target_capacity, elb)
        return True
    
    # nothing happened
    return False


# hint: write a PR if you have more than:
#          - 400 ELBs
#       paging isn't implemented intentionaly for now
def lambda_handler(event, context):
    elbapi = boto3.client('elb')
    ec2api = boto3.client('ec2')
    cwapi = boto3.client('cloudwatch')
    
    # retrieve metadata about all ELBs
    elbs_response = elbapi.describe_load_balancers()
    if not elbs_response['LoadBalancerDescriptions']:
        logger.info('No ElasticLoadBalancers found. Aborting execution.')
        return
        
    tags_response = elbapi.describe_tags(LoadBalancerNames=[elb['LoadBalancerName'] for elb in elbs_response['LoadBalancerDescriptions']])
    
    for elb in tags_response['TagDescriptions']:
        tags = {tag['Key']: tag['Value'] for tag in elb['Tags']}
        
        if 'SpotFleetRequestId' not in tags:
            continue
        
        scaled = scale(elb['LoadBalancerName'], 'Up', +1, tags, cwapi, ec2api, elbapi)
        if scaled:
            continue
        
        scaled = scale(elb['LoadBalancerName'], 'Down', -1, tags, cwapi, ec2api, elbapi)
        if scaled:
            continue
            
        logger.info("No changes for ELB %s", elb['LoadBalancerName'])
