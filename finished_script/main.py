import argparse
import boto3
import ipaddress
import math
import sys
from natsort import natsorted
from typing import List, Set, Tuple

client = boto3.client('ec2', region_name='us-west-2')


def main(args: argparse.Namespace) -> None:
    # 1st iteration:
    print('VPC CIDR: {}'.format(get_vpc_cidr(args.vpcid)))
    print('Subnet CIDRs: {}'.format(get_subnet_cidrs(args.vpcid)))

    # 2nd iteration:
    free_cidrs = [str(network) for network in get_free_cidrs(args.vpcid)]
    natsorted(free_cidrs)
    free_cidrs.reverse()
    print('Free CIDRs in VPC: {}'.format(free_cidrs))

    min_ip, max_ip = get_free_ips_min_max(args.vpcid)
    print('Free IPs in VPC (minus network address and broadcast address) range from {} to {}'.format(min_ip, max_ip))

    # 3rd iteration:
    print('Number of available subnets of size /{} in VPC: {}'.format(args.subnetsize, get_available_subnets_of_size(args.vpcid, int(args.subnetsize))))


def get_vpc_cidr(vpc_id: str) -> List[str]:
    res = client.describe_vpcs(VpcIds=[vpc_id])
    for vpc in res['Vpcs']:
        cidr = vpc['CidrBlock']
        return cidr


def get_subnet_cidrs(vpc_id: str) -> List[str]:
    res = client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    return [subnet['CidrBlock'] for subnet in res['Subnets']]


def get_free_cidrs(vpc_id: str) -> List[ipaddress.IPv4Network]:
    vpc_cidr = get_vpc_cidr(vpc_id)
    subnet_cidrs = get_subnet_cidrs(vpc_id)
    vpc_network = ipaddress.ip_network(vpc_cidr)

    free_networks: List[ipaddress.IPv4Network] = [vpc_network]

    for subnet_cidr in subnet_cidrs:
        subnet_network = ipaddress.ip_network(subnet_cidr)

        for free_network in free_networks:
            subtraction_result = subtract_network(free_network, subnet_network)

            if is_same_network(free_network, subnet_network) or len(subtraction_result) != 0:
                free_networks.remove(free_network)

            free_networks.extend(subtraction_result)

    return free_networks


def get_free_ips_min_max(vpc_id: str) -> Tuple[str, str]:
    hosts_set = get_host_ips(vpc_id)
    return str(min(hosts_set)), str(max(hosts_set))


def get_available_subnets_of_size(vpc_id: str, netmask: int) -> int:
    vpc_available_hosts_count = len(get_host_ips(vpc_id))
    subnet_hosts_count = math.pow(2, (32 - netmask))

    return math.floor(vpc_available_hosts_count/subnet_hosts_count)


def get_host_ips(vpc_id: str) -> Set[ipaddress.IPv4Address]:
    hosts: List[ipaddress.IPv4Address] = []

    for cidr in get_free_cidrs(vpc_id):
        hosts.extend(list(cidr.hosts()))

    return set(hosts)


def subtract_network(
    container_network: ipaddress.IPv4Network,
    contained_network: ipaddress.IPv4Network
) -> List[ipaddress.IPv4Network]:
    if contained_network.subnet_of(container_network):
        return list(container_network.address_exclude(contained_network))

    return []


def is_same_network(net1: ipaddress.IPv4Network, net2: ipaddress.IPv4Network) -> bool:
    if net1.compare_networks(net2) == 0:
        return True
    return False


def parse_args(args: List[str] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--vpcid', help='VPC ID', required=True)
    parser.add_argument('--subnetsize', help='subnet net mask as integer', required=True)
    return parser.parse_args(args)


if __name__ == '__main__':
    # print(sys.argv)
    args = parse_args(sys.argv[1:])
    main(args)
