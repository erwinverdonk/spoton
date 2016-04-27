import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_spot_fleet_request_id_tag(tag_description):
    ids = [tag['Value'] for tag in tag_description['Tags'] if tag['Key'] == 'SpotFleetRequestId']
    if ids:
        return ids[0]
    else:
        return None

# hint: write a PR if you have more than:
#          - 400 ELBs
#          - 1000 instances through spot fleet requests
#       paging isn't implemented intentionaly for now
def lambda_handler(event, context):
    elbapi = boto3.client('elb')
    ec2api = boto3.client('ec2')
    
    # retrieve metadata about all ELBs
    elbs_response = elbapi.describe_load_balancers()
    if not elbs_response['LoadBalancerDescriptions']:
        logger.info('No ElasticLoadBalancers found. Aborting execution.')
        return
        
    tags_response = elbapi.describe_tags(LoadBalancerNames=[elb['LoadBalancerName'] for elb in elbs_response['LoadBalancerDescriptions']])
    
    # extract ELBs that have the SpotFleetRequestId tag
    elbs = {elb['LoadBalancerName']: get_spot_fleet_request_id_tag(elb) for elb in tags_response['TagDescriptions']}
    elbs = {k: v for k, v in elbs.items() if v}
    
    if not elbs:
        logger.info('No ElasticLoadBalancer found that is connected to a SpotFleetRequest. Aborting execution.')
        return
    
    # sync all ELBs that are connected via the tag:
    for elb_name, sfr_id in elbs.items():
        
        # get current state of instances in the spot fleet request and the ELB
        sfr_response = ec2api.describe_spot_fleet_instances(SpotFleetRequestId=sfr_id)
        elb_response = elbapi.describe_instance_health(LoadBalancerName=elb_name)
        
        sfr_instances = [instance['InstanceId'] for instance in sfr_response['ActiveInstances']]
        elb_instances = [instance['InstanceId'] for instance in elb_response['InstanceStates']]
        
        # compare instance lists
        instances_to_register = list(set(sfr_instances) - set(elb_instances))
        instances_to_deregister = list(set(elb_instances) - set(sfr_instances))
        instances_to_stay = list(set(elb_instances) - set(instances_to_deregister))
        
        # health check of instances before registering
        if instances_to_register:
            instances_health_response = ec2api.describe_instance_status(InstanceIds=instances_to_register, IncludeAllInstances=False)
            instances_to_register = [status['InstanceId'] for status in instances_health_response['InstanceStatuses']] # only running instances are returned, no further checks currently
        
        # TODO allow instances to tag themself to be ignored for ELB registration (instance can add this tag on shutdown to prevent dead intances in ELB): check_instances_to_stay
        
        # sync elb!
        if instances_to_register:
            elbapi.register_instances_with_load_balancer(LoadBalancerName=elb_name, Instances=[{'InstanceId': instance_id} for instance_id in instances_to_register])
            logger.info('Instances registered with ELB %s: %s', elb_name, instances_to_register)
            
        if instances_to_deregister:
            elbapi.deregister_instances_from_load_balancer(LoadBalancerName=elb_name, Instances=[{'InstanceId': instance_id} for instance_id in instances_to_deregister])
            logger.info('Instances deregistered from ELB %s: %s', elb_name, instances_to_deregister)
            
        if not instances_to_register and not instances_to_deregister:
            logger.info('No changes for ELB %s', elb_name)
