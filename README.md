# OpenVPN Setup on Ubuntu 20.04 Server and Client Machine

## Requirements

### Important files

Python script to provision virtual machine, create port forwards and install OpenVPN Cloud-init.

```bash
openvpn_installer.py
```

### Set environment variables in your shell (Linux / Mac)

```bash
export MY_JWT = ""
```

### Copy public your public ssh key into openvpn/openvpn_installer folder to enable you to access the server remotely after  installation

```bash
cp <ssh_pub_key> openvpn/openvpn_installer/
```

## Running the Python Scripts

The scripts can run in any Python 3 environment. In this case, a docker container based on the GiG docker tools image will be used.

## Create docker image

### Clone GIG Tools docker repository

```bash
git clone git@github.com:gig-tech/GIG-Docker-Tools.git
```

### Set environment variables

```bash
ARG_JWT=

ARG_VCO_API_URL=

export ARG_JWT

export ARG_VCO_API_URL
```

### Build Image

```bash
cd gig_tools/cli_terraform

docker build --build-arg ARG_JWT --build-arg ARG_VCO_API_URL -t <vco_name> .
```

### Clone OpenVPN repository

```bash
cd <working_dir>

git clone git@github.com:gig-tech/OpenVPN.git

cd openvpn
```

### Important Note

* Add your JWT to env_list file variable -> MY_JWT= using your favorite editor.

### Run container and script to set up OpenVPN server

```bash
docker run --env-file env_list -w /root/home/ --mount type=bind,source=$PWD,target=/root/home -i -t <vco_name> /bin/bash

pip3 install pipenv

pipenv shell

pip3 install requests paramiko scp click 

python3 openvpn_installer/openvpn_installer.py deploy-server --help
```

## Create and download client1.ovpn

Installation of OpenVPN takes about five minutes. This command will not work until the installation is complete. You will get "..File not found!" message if attempted before 5 mins have elapsed.

```bash
python3 openvpn_installer/openvpn_installer.py --help
```

## Transfer client file to Windows and Linux machines

### For windows
    
* Import client file into VPN client.
    
### Linux Client
   
* Install OpenVPN client using

```bash
sudo apt update

sudo apt install -y openvpn resolvconf openvpn-systemd-resolved easy-rsa

openvpn --config client1.ovpn # Place your client1.ovpn file in your current directory
```

* If systemd-resolved - comment out the following block of code in the client config file

```bash
script-security 2

up /etc/openvpn/update-systemd-resolved

down /etc/openvpn/update-systemd-resolved

down-pre

dhcp-option DOMAIN-ROUTE .
```

 * Or update-resolv-conf - comment out the following block of code in the client config file
 
```bash
script-security 2

up /etc/openvpn/update-resolv-conf

down /etc/openvpn/update-resolv-conf
```

## Try and ping the server on private IP in the cloudspace

```bash
ping xyx.xyx.xyx.xyz
```
