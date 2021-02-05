import boto3
import sys
import argparse
from pprint import pprint
from typing import List

client = boto3.client('ec2', region_name='us-west-2')


def main(args) -> None:
    pass
    # 1st iteration
    print('VPC CIDR: {}'.format(get_vpc_cidr(args.vpcid)))
    print('Subnet CIDRs in VPC: {}'.format(get_subnet_cidrs(args.vpcid)))

    # 2nd iteration

    # 3rd iteration


def get_vpc_cidr(vpcid: str) -> str:
    res = client.describe_vpcs(VpcIds=[vpcid])
    cidr = res['Vpcs'][0]['CidrBlock']
    return cidr


def get_subnet_cidrs(vpcid: str) -> List[str]:
    res = client.describe_subnets(
        Filters=[
            {
                'Name': 'vpc-id',
                'Values': [
                    vpcid,
                ]
            },
        ]
    )

    subnets = res['Subnets']
    cidrs: List[str] = []

    for subnet in subnets:
        cidrs.append(subnet['CidrBlock'])

    return cidrs


def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('--vpcid', help='VPC ID', required=True)
    # parser.add_argument('--subnetsize', help='subnet net mask as integer', required=True)
    return parser.parse_args(args)


if __name__ == '__main__':
    args = parse_args(sys.argv[1:])
    main(args)
