from setuptools import setup

setup(
    name='openvpn-installer',
    version='0.1',
    author='Eric Mugerwa',
    author_email='eric@gigi.tech',
    description='openvp-installer is a tool to install and configure openvpn on Ubuntu 20.04 Server on Gig.Tech based clouds',
    license='GPLv3+',
    packages=[openvpn_installer],
    url='https://git.gig.tech/gigimages/images/openvpn',
    install_requires=[
        'click',
        'paramiko',
        'scp',
        'requests'
    ],
    entry_points='''
        [console_scripts]
        openvpn_installer=openvpn_installer.openvpn_installer:cli
    '''

)