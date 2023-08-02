import time
import requests
# import os
import json
import base64
import paramiko
from paramiko import SSHClient
from scp import SCPClient
from scp import get
import pdb
import click

JWT = <JWT_TOKEN>
headers = {'Authorization': 'bearer %s' % JWT}

# Create VM

@click.group()
def cli():
    "OPENVPN Installer for GiG.tech based clouds"
    pass
@cli.command('deploy-server')
@click.argument('vco_domain')
@click.argument('customer_id')
@click.argument('cloudspace_id')
@click.argument('image_id')
@click.argument('pub_ssh_port' )
@click.argument('pub_openvpn_port' )
@click.argument('pub_key')
def deploy_server(vco_domain, customer_id, cloudspace_id, image_id, pub_ssh_port, pub_openvpn_port, pub_key="abc"):
    print("Checks before VM Creation")
    print(f"Checking if public ssh port {pub_ssh_port} is unused on the cloudspace")
    ssh_port_used = check_port(customer_id, cloudspace_id, vco_domain, pub_ssh_port)
    if ssh_port_used == -1:
        print("Operation unauthorised, set JWT in environment variables.")
        return
    if ssh_port_used:
        print(f"port {pub_ssh_port} is already used on the cloudspace, choose another")
        return
    print(f"{pub_ssh_port} is available continuing with the deployment")
    print(f"Checking if public openvpn port {pub_openvpn_port} is unused on the cloudspace")
    openvpn_port_used = check_port(customer_id, cloudspace_id, vco_domain, pub_openvpn_port)
    if openvpn_port_used:
        print(f"port {pub_openvpn_port} is already used on the cloudspace, choose another")
        return
    print(f"{pub_openvpn_port} is available continuing with the deployment")
    "Launch OPENVPN server"
    b64_cmds_server = base64_encode("cmds_server")
    b64_cmds_client = base64_encode("cmds_client")
    try:
        if (pub_key):
            with open(pub_key) as f:
                ssh_pub_key = f.read()
    except:
        print(f"WARNING: {pub_key} not found, use password to access server")
        # ssh_pub_key="abc"

    vm_attribs = {
        "name": "vpn-server",
        "description": "OpenVPN Access Server",
        "vcpus": 1,
        "memory": 1024,
        "image_id": image_id,
        "disk_size": 10,
        "os_type": "Linux",
        "os_name": "Ubuntu server 20.04",
        "enable_vm_agent": True,
        "customer_id": customer_id,
        "cloudspace_id": cloudspace_id#,
        # "user_data": "{write_files: [{content: IyEvYmluL2Jhc2gKIyBEb3dubG9hZCBpbnN0YWxsIGFuZCBjb25maWcgc2NyaXB0cwoKIyMgU2VydmVyIGluc3RhbGwKY2QgL3Jvb3QvCmN1cmwgaHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL3dhbmRhbGFicy9vcGVudnBuL21haW4vY21kc19zZXJ2ZXIgLU8KY2htb2QgK3ggY21kc19zZXJ2ZXIKLi9jbWRzX3NlcnZlcgoKIyMgQ2xpZW50IG92cG4gZmlsZSBnZW5lcmF0aW9uCmNkIC9ob21lL3VzZXIvY2xpZW50LWNvbmZpZ3MKY3VybCBodHRwczovL3Jhdy5naXRodWJ1c2VyY29udGVudC5jb20vd2FuZGFsYWJzL29wZW52cG4vbWFpbi9jbWRzX2NsaWVudCAtTwpjaG1vZCAreCBjbWRzX2NsaWVudAo=, encoding: b64, path: /var/lib/cloud/scripts/per-once/openvpn_install, permissions: '0755'}]}"
    }
    payload = {
        "userdata": {
            "users": [
                {
                    "name": "root",
                    "shell": "/bin/bash",
                    "ssh-authorized-keys": ssh_pub_key
                }
            ],
            "write_files": [
                {
                    "content": b64_cmds_server,
                    "encoding": "b64",
                    "path": "/var/lib/cloud/scripts/per-once/cmds_server",
                    "permissions": "0755"
                },
                {
                    "content": b64_cmds_client,
                    "encoding": "b64",
                    "path": "/home/user/client-configs/cmds_client",
                    "permissions": "0755"
                }
            ],
            "bootcmd": [
                "sed -i 's/1/0/g' /etc/apt/apt.conf.d/20auto-upgrades" 
            ]
        }
    }
    print("\n[1] Creating VM ...")
    create_vm_url = f"https://{vco_domain}/api/1/customers/{customer_id}/cloudspaces/{cloudspace_id}/vms"
    # new_vm = requests.post(create_vm_url, headers=headers, params=vm_attribs)
    new_vm = requests.post(create_vm_url, headers=headers, params=vm_attribs, json=payload)
    try:
        id = new_vm.json()["vm_id"]
    except:
        print('vm was not created successfully, please check your jwt token or api endpoint'  )
        return
    print("\n    Creating VM completed.")

    print("\n[2] Creating  Port Forwards ...")
    try:
        create_port_forward(22, pub_ssh_port, "tcp", id, customer_id, cloudspace_id, vco_domain)
        print("\n    SSH Port Forwards created.")
    except:
        print("check to see if selected ssh public port is free")
        return
    
    try:
        create_port_forward(1194, pub_openvpn_port, "udp", id, customer_id, cloudspace_id, vco_domain)
        print("\n    OpenVPN Port Forwards created")
    except:
        print("check to see if selected public ports are free")
        return
    print("\n    VM creation completed, please wait for a few minutes for the OpenVPN server to completely install before creating a user.\n")


# Create Port Forwards

def create_port_forward(local_port, public_port, protocol, vm_id, customer_id, cloudspace_id,vco_domain):
    pf_post_attrib = {
        "protocol": protocol,
        "local_port": local_port,
        "vm_id": vm_id,
        "public_port": public_port,
        "customer_id": customer_id,
        "cloudspace_id": cloudspace_id
    }
    create_pf_url = f"https://{vco_domain}/api/1/customers/{customer_id}/cloudspaces/{cloudspace_id}/portforwards"
    pf_post_resp = requests.post(create_pf_url, headers=headers, params=pf_post_attrib)

def check_port(customer_id, cloudspace_id, vco_domain, port):
    pf_get_attrib = {
        "cloudspace_id": cloudspace_id,
        "customer_id": customer_id
    }
    get_pf_url = f"https://{vco_domain}/api/1/customers/{customer_id}/cloudspaces/{cloudspace_id}/portforwards"
    pf_get_resp = requests.get(get_pf_url, headers=headers, params=pf_get_attrib)
    if pf_get_resp == '<Response [401]>':
        return -1
    for pf in pf_get_resp.json()["result"]:
        # if pf:
        #     return pf
        return pf["public_port"] == int(port)
       
def base64_encode(file_name):
    text = open(file_name, "r").read()
    text_bytes = text.encode('utf-8')
    text_base64_bytes = base64.b64encode(text_bytes)
    return text_base64_bytes.decode("utf-8")



# Download client config

@cli.command("create-user")
@click.argument("vco_domain")
@click.argument("customer_id")
@click.argument("cloudspace_id")
@click.argument("external_ip")
@click.argument("vm_id")
@click.argument("pub_ssh_port")
@click.argument("user_name")
def create_user(vco_domain, customer_id, cloudspace_id, external_ip, vm_id, pub_ssh_port, user_name):
    # ext_net_ip = get_cloudspace_public_ip(customer_id, cloudspace_id, external_network_id, vco_domain)
    ssh_password = get_password(vm_id, customer_id, cloudspace_id, vco_domain)
    if ssh_password == -1:
        print("Operation unauthorised, set JWT in environment variables")
    client = SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(external_ip, port=pub_ssh_port, username="user", password=ssh_password, timeout=5)

    def create_user_config():
        print(f"\n[1] Creating user - {user_name}")
        client.exec_command(f"sudo cp client-configs/cmds_client {user_name}_client")
        client.exec_command(f"sudo sed -i 's/client1/{user_name}/g' {user_name}_client")
        client.exec_command(f"sudo ./{user_name}_client")
        time.sleep(5)
        print(f"\n    User {user_name} creation completed.")
    
    def download_user_config():
        scp = SCPClient(client.get_transport())
        file_name = f"{user_name}"+".ovpn"
        try:
            print(f"\n[2] Downloading {user_name} client user config file.")
            scp.get(file_name)
            scp.close()
            client.exec_command(f"sudo rm {user_name}*")
            print(f"\n    {file_name} downloaded succesfully\n")
        except:
            print(f"{file_name}: File not found. Wait a few minutes for the installation to complete.")

    create_user_config()
    download_user_config()


def get_password(vm_id, customer_id, cloudspace_id,vco_domain):
    vm_attrib = {
        "vm_id": vm_id,
        "customer_id": customer_id,
        "cloudspace_id": cloudspace_id
    }
    get_vm_url = f"https://{vco_domain}/api/1/customers/{customer_id}/cloudspaces/{cloudspace_id}/vms/{vm_id}"
    vm = requests.get(get_vm_url, headers=headers, params=vm_attrib)
    if vm == '<Response [401]>':
        return -1
    return  vm.json()["os_accounts"][0]["password"]


# def get_cloudspace_public_ip(customer_id, cloudspace_id, external_network_id, vco_domain):
#     cs_extnet_attrib = {
#         "cloudspace_id": cloudspace_id,
#         "customer_id": customer_id
#     }
#     get_pf_url = f"https://{vco_domain}/api/1/customers/{customer_id}/cloudspaces/{cloudspace_id}/external-networks"
#     cs_extnet_resp = requests.get(get_pf_url, headers=headers, params=cs_extnet_attrib)
#     for extnet in cs_extnet_resp.json()["result"]:
#         if extnet["external_network_id"] == external_network_id:
#             ip_addr = extnet["external_network_ip"][0:-3]
#             return ip_addr
#     return -1


if __name__ == '__main__':

    cli()

