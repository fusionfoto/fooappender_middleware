# SwiftStack: Test Environment Setup

Welcome to *one possible* method for setting up a small object storage test or development environment, on your own laptop, using SwiftStack.

There are, unsurprisingly, many, many ways of doing this. 

In this doc we're looking at the most manual way possible, because - being so manual - it is appliable to anyone who would like to set up a test environment, using an on-premises SwiftStack controller, regardless of the toolchain they use.

That's not to say you shouldn't automate everything with Selenium, or run it in Vagrant, or containerize it, or whatever, if you want to. Feel free!

If you do follow this guide, I'd suggest running it once, then making templates out of your VMs, and then giving them to other folks at your company.

Once you have finished the install guide here, you'll end up with...

 - One SwiftStack controller (the management plane for SwiftStack)
 - One SwiftStack storage node (where objects actually end up)

...both of these will end up on a private, NAT-ed network so that you can work with them irrespective of where your computer happens to be. 

If you already have a dev setup, and you'd just like to know where the endpoints are - perhaps someone gave you a VM template(!) - then you can find the API endpoints you might be interested in right at the end of this doc.

## Network Setup

Set up a virtual NAT network for your hosts to use. I’m going to use 192.168.13.0 in the examples below. In our virtual network, our hosts will look like this:

 - SwiftStack Controller (ssc.swiftstackdev.example.com): 192.168.13.10
 - SwiftStack Storage Node (paco1.swiftstackdev.example.com): 192.168.13.21

When we're done your object store will be running on an entirely private network that won't touch or conflict with anything else you plug your laptop into. The downside is that you'll need to set up port forwards to access services on it as we'll get to below.

- Fire up virtualbox.
- Navigate to Preferences >> Network.
- Add a new network with a CIDR of 192.168.13.0/24 as below.

![natnetwork](https://cloud.swiftstack.com/v1/AUTH_straill/voxygen/natnetwork.png)

- Save the settings.


To finish up, we need to set up port forwarding rules. Create the following shell script:

```
ssc_ipv4=192.168.13.10
ssc_prefix=20              # We need to start local port forwards above 1022!
paco1_ipv4=192.168.13.21
paco1_prefix=21
network=SwiftStackDev

case $1 in 
  'start') 
    VBoxManage natnetwork modify --netname ${network} --port-forward-4 "ssh_ssc:tcp:[]:${ssc_prefix}22:[${ssc_ipv4}]:22" 
    VBoxManage natnetwork modify --netname ${network} --port-forward-4 "http_ssc:tcp:[]:${ssc_prefix}80:[${ssc_ipv4}]:80" 
    VBoxManage natnetwork modify --netname ${network} --port-forward-4 "https_ssc:tcp:[]:${ssc_prefix}443:[${ssc_ipv4}]:443" 
    VBoxManage natnetwork modify --netname ${network} --port-forward-4 "ssh_paco1:tcp:[]:${paco1_prefix}22:[${paco1_ipv4}]:22" 
    VBoxManage natnetwork modify --netname ${network} --port-forward-4 "http_paco1:tcp:[]:${paco1_prefix}80:[${paco1_ipv4}]:80" 
    VBoxManage natnetwork modify --netname ${network} --port-forward-4 "https_paco1:tcp:[]:${paco1_prefix}443:[${paco1_ipv4}]:443" 
    ;;
   'stop') 
    VBoxManage natnetwork modify --netname ${network} --port-forward-4  delete ssh_ssc
    VBoxManage natnetwork modify --netname ${network} --port-forward-4  delete http_ssc
    VBoxManage natnetwork modify --netname ${network} --port-forward-4  delete https_ssc
    VBoxManage natnetwork modify --netname ${network} --port-forward-4  delete ssh_paco1
    VBoxManage natnetwork modify --netname ${network} --port-forward-4  delete http_paco1
    VBoxManage natnetwork modify --netname ${network} --port-forward-4  delete https_paco1
     ;;
   *)
     ;;
esac

```

...and run it:

```
$ sh natnetwork.sh start
```

...which will add a load of port forwards for you. To remove them, run the sccript again but with a `stop` argument.

## Virtual Machines - OS Setup
We're going to set up two VMs using the network we just created.

 - **ssc.swiftstackdev.example.com** (192.168.13.10): A SwiftStack Controller VM. This machine will run Centos 7, and have 1 vCPU, 2GB RAM.  
 - **paco1.swiftstackdev.example.com** (192.168.13.21): A SwiftStack storage node. The VM will run Ubuntu 14.04, have 1vCPU and 2GB RAM, and have an extra 10 1GB virtual disks for storage.

### Controller OS Install

> #### TL;DR
> - Set up a fresh Centos 7 machine with...
>   - 1 VPU, 2 GB RAM, 1 OS disk with >= 40GB space;
>   - One NIC attached to the "SwiftStackDev" NAT network set up above;
>   - Set the NIC IP to 192.168.13.10/24, and use 192.168.13.1 as the gateway and DNS server. Set the FQDN to ssc.swiftstackdev.example.com. Ensure these settings are persistent across reboots.
>  - We only want a minimal install, and we only need a root user.
>  - Snapshot it when done so you never need to build it again.

Provision a new Centos 7 64 bit machine:

 - New Virtual Machine.
 - Set **name** to **ssc.swiftstackdev.example.com**, **type** to **Linux**, **Version** to **Red Hat (64 bit)**, and hit continue.
 - Set RAM to 2048 MB (2GB).
 - When prompted, select "Create a virtual harddisk now".
 - Select "VDI" for the hard disk type.
 - Select "dynamically allocated".
 - Set the disk size to 40GB.
 - Select the new VM, and hit **Settings**.
 - In the **Storage** tab, mount your Centos 7 ISO on the IDE secondary master as below:

![centos_iso](https://cloud.swiftstack.com/v1/AUTH_straill/voxygen/ide_secondary_master.png)

 - In the **Network** tab, ensure **adaptor 1** is **enabled**, attach it to a "NAT Network", and then select the **SwiftStackDev** network we setup earlier - as below.

![natnetwork_ssc](https://cloud.swiftstack.com/v1/AUTH_straill/voxygen/natnetwork_ssc.png)

 - Hit **OK** to save yout settings, then boot the VM (select it, and click **Start**) to install Centos 7.
 
 You'll now need to install Centos 7. From the booted VM, do this:
 
  - Select **Install Centos 7** when prompted
  - Make whatever language selections you feel appropriate.
  - We want a minimal OS install, so won't be changing too much.
  - Select the install drive, with automatic paritioning: **System** >> **Installation Destination**; click this, select your 40GB harddrive, and tick "done";
  - Setup networking: **System** >> **Network and Hostname**.
  - Set a hostname of **ssc.swiftstackdev.example.com**.
  - Select your single network adaptor, click Configure, and then add:
     - An IPV4 address of **192.168.13.10/24**
     - A default route of **192.168.13.1**
     - A DNS server at **192.168.13.1**

...Virtualbox will add a virtual router / DNS proxy at 192.168.13.1 for us, which is what we're using above. The network setup should look like this:
      
![centos_7_nic_setup](https://cloud.swiftstack.com/v1/AUTH_straill/voxygen/centos_nic_setup.png)

 - Save your network config.
 - Hit "Begin Installation".
 - Set whatever root password you like. You don't need to add any other users.
 - After the machine completes, ensure the NIC is set to start on boot by editing `/etc/sysconfig/network-scripts/ifcfg-enp0s3` and setting the line
```
ONBOOT=no
```

to 

```
ONBOOT=yes
```

 - ...at which point, I expect, you'll need to run `ifup enp0s3` to bring the NIC up.

From this point forwards, you'll be able to log into the machine with 

```
$ ssh -p 2022 root@localhost
```

 - Finally, add a useful /etc/hosts file like the below:

```
127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4
::1         localhost localhost.localdomain localhost6 localhost6.localdomain6
192.168.13.10 ssc   ssc.swiftstackdev.example.com
192.168.13.21 paco1 paco1.swiftstackdev.example.com
```

You may want to snapshot your VM here. Now move on to the storage node OS install.

 
### Storage Node (PACO) OS Install


> #### TL;DR
> - Set up a fresh Ubuntu 14.04 machine with...
>   - 1 VPU, 2 GB RAM, 1 OS disk with >= 40GB space;
>   - Some number (I chose 10) of additional 1GB disks, which we won't mount ourselves;
>   - One NIC attached to the "SwiftStackDev" NAT network set up above;
>   - Set the NIC IP to 192.168.13.21/24, and use 192.168.13.1 as the gateway and DNS server. Set the FQDN to paco1.swiftstackdev.example.com. Ensure these settings are persistent across reboots.
>  - We only want a minimal install, and we only need a root user.
>  - Snapshot it when done so you never need to build it again.

Provision a new Ubuntu 14.04 64 bit machine:

 - New Virtual Machine.
 - Set **name** to **paco1.swiftstackdev.example.com**, **type** to **Linux**, **Version** to **Ubuntu (64 bit)**, and hit continue.
 - Set RAM to 2048 MB (2GB).
 - When prompted, select "Create a virtual harddisk now".
 - Select "VDI" for the hard disk type.
 - Select "dynamically allocated".
 - Set the disk size to 40GB.
 - Select the new VM, and hit **Settings**.

Storage setup for our node is slightly more interesting than the controller. We need to add some disks to store objects on!

 - In the **Storage** tab, mount your Ubuntu 14.04 ISO on the IDE secondary master. I'm using a desktop ISO below... this probably isn't the best choice, but it'll do. Feel free to use 14.04 server instead.
 - In addition to the boot disk, add 10 1GB disks to the SATA controller. All of these should be dynamically allocated VDIs.

Your **storage** tab should end up looking like this:

![ubuntu_disks](https://cloud.swiftstack.com/v1/AUTH_straill/voxygen/ubuntu_disks.png)

 - In the **Network** tab, ensure **adaptor 1** is **enabled**, attach it to a "NAT Network", and then select the **SwiftStackDev** network we setup earlier - as below.

![natnetwork_ssc](https://cloud.swiftstack.com/v1/AUTH_straill/voxygen/ubuntu_network.png)

 - Hit **OK** to save yout settings, then boot the VM (select it, and click **Start**) to start installing Ubuntu 14.04.
 
You'll now need to install Ubuntu. I've used the desktop ISO for this, so your setup may vary somewhat if using the server variant. From the booted VM, do this:
 
  - Select **Install Ubuntu** when prompted
  - Hit **Continue**
  - Select **Erase Disk and Install Ubuntu**; hit **Continue**
  - Select your 40GB drive (it should already be selected) from the drive dropdown;
  - Hit **Install Now**, then **Continue**
  - Select your prefered timezone and locale .
  - When promoted set **Your name** to `swiftstack`
  - Set **Your computer's name** to `paco1.swiftstackdev.example.com`
  - Set a password and hit **Continue**.

Once the OS had finished installing, reboot and set up a few more things:

 - Log in as `swiftstack`, then `sudo su -` to become the `root` user.
 - Set up a static IPV4. Make the content of /etc/network/interfaces the below:
```
# interfaces(5) file used by ifup(8) and ifdown(8)
auto lo
iface lo inet loopback

auto eth0
iface eth0 inet static
  address 192.168.13.21
  netmask 255.255.255.0
  gateway 192.168.13.1
  dns-nameservers 192.168.13.1
```

 - Reboot the VM to apply the changes.
 - Install SSH server:

```
$ sudo apt-get install openssh-server
```
 - Set a root password (if wanted) with `$ passwd root`. If you're not using ssh keys, you'll also at this point want to enable root login with a password by editing `/etc/ssh/sshd_config`, changing `PermitRootLogin = without-password` to `PermitRootLogin = yes`, and running `sudo service ssh restart`.

At this point you should be able to log in from your laptop with 

```
$ ssh -p 2122 root@localhost
```

...do so, then complete the setup by adding a suitable /etc/hosts file:

```
127.0.0.1       localhost
127.0.1.1       paco1.swiftstackdev.example.com paco1
192.168.13.10   ssc ssc.swiftstackdev.example.com

# The following lines are desirable for IPv6 capable hosts
::1     ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
```

As with the controller, you may want to snapshot your VM here. Now move on to the  SwiftStack install below.


## Virtual Machines: SwiftStack Setup
We now have two VMs with fresh OS installs. We're going to install the SwiftStack controller software on the Centos 7 VM, and use it to install SwiftStack storage node software on the Ubuntu 14.04 VM.

You'll need two things before proceeding here:

 - A SwiftStack installer tarball. On your portal page (https://portal.swiftstack.com, under the “Downloads” tab, you'll find a download URL for the current release (below we use 5.9.0.3). In general, we suggest you use the same release as in your pre-prod environment(s) - you may need to ask your ops team for a copy.
 - You’ll also want a copy of the license file. You will need to ask your ops team for this. 


### SwiftStack Controller Install

- Log in to your controller via your SSH port forward.

```
$ ssh -p 2022 root@localhost
```
 - Pull the *correct* version of the SwiftStack controller software to a temporary folder using cURL. 
 - The *correct* version is up to you, but is probably whatever version you run in your preprod - staging - environment.
 - Below we use **5.9.0.3**; the URL can be found using your account at **https://portal.swiftstack.com**.
 - You may need to ask your Ops team if you need to use an earlier version of the binary.

```
$ cd /tmp
$ curl -o SwiftStack-Controller-5.9.0.2-installer.sh  https://storage101.dfw1.clouddrive.com/v1/MossoCloudFS_4fe70b92-31ee-4a4e-88a9-c8493eb9c579/onprem_updates/SwiftStack-Controller-5.9.0.2-installer.sh?temp_url_sig=0d84be79e8cf49705ad2189c2383b52acf8f4bc6&temp_url_expires=1508577081
```

Once you have it, run it (as root):

```
# sh ./SwiftStack-Controller-5.9.0.3-installer.sh 
```

Once it completes, log into the web UI. The controller spits out an address to use; if you're setting up a local dev environment, this won't work, because of your NAT network setup. Instead, use https://localhost:20443.

Either way, log in as **localadmin**, password **password**. Then, complete the setup in the web UI:

- Upload your controller license file;
- Set the **local hostname** to **ssc.swiftstackdev.example.com**
- Set a password for the **localadmin** user;
- For a test environment (**not production**) ensure that **Insecure Fake Entropy** is **checked**;
- Leave everything else at default, and hit **Submit**.

The UI will perform some setup tasks and may ask you to refresh your page. Once it completes, set up your test cluster:

 - Log in as localadmin at the web UI - https://localhost:20443 for a dev setup.
 - **You will see a license warning** in all likelihood. For a test, or a dev enironment, you can safely ignore this.
 - Hit **Clusters** in the top right nav bar to start setting up a storage cluster.
 - Add a name - I chose **test**; select **Testing** from the **Deployment Status** dropdown, and hit **Create Cluster**:

![create_cluster](https://cloud.swiftstack.com/v1/AUTH_straill/voxygen/create_cluster.png)

You'll be taken to the **Configuration** screen.

 - For a dev setup you should leave most things alone apart from the network settings; select **No Load Balancer** and set **Cluster API IP Address** to **192.168.13.21** - the IP of your one storage node.

![network_ssc](https://cloud.swiftstack.com/v1/AUTH_straill/voxygen/network_config.png)

 - Hit **Submit Changes**.


Before moving on to our node, we need to add a Swift user. In the example below I use a single user - **swift** - who can access any storage account (is a *superuser*).
 - Hit **Clusters** in the top nav bar.
 - Find your *test* cluster and hit **Users**.
 - Click **Create new user**.
 - Set **username** to **swift**, a password as you want, and make sure both **Superuser** and **Enabled** are **checked**.
 - Hit **Submit**.

We're now ready to set up our storage node.

### SwiftStack Storage Node (PACO) Install
Ingesting a storage node is made more interesting by the fact that our SwiftStack Controller's TLS certificate is self-signed. 

We need to do the following:

 - Make Ubuntu accept our controller's (self-signed) TLS certificate;
 - Install the swiftstack software using the controller;
 - *Ingest* the node into our *test* cluster;
 - Configure the storage node;
 - Deploy our config to the cluster.

First up, we need to accept the TLS cert held by the controller. Let's use openssl. Log into paco1 as root via your port forwarding rules:

```
ssh -p 2122 root@localhost
```

Now scrape and accept the contoller cert:

```
$ echo -n | openssl s_client -connect ssc.swiftstackdev.example.com:443 | sed -ne '/-BEGIN CERTIFICATE-/,/-END CERTIFICATE-/p' > /usr/local/share/ca-certificates/ssman.crt
$ update-ca-certificates
```

Check the validity of your cert. The below should *not* print any output (though in the example here, it does...):

```
# curl https://ssc.swiftstackdev.example.com/install
curl: (51) SSL: certificate subject name 'development.lan.mycompany.com' does not match target host name 'ssc.swiftstackdev.example.com'
```

> **IMPORTANT!** The hostname (*CN*) on the cert is driven by your license. If 
> you see output like the above - and I expect you will - you **must** use the CN on the cert for the node installation. 
>
> With the example above, I need to add `development.lan.mycompany.com` to our entry for the controller in /etc/hosts:
> 
> ```192.168.13.10   ssc ssc.swiftstackdev.example.com development.lan.voxygen.com```
> 
> ...and then proceed to install the node software, using `development.lan.mycompany.com` in the cURL command. See below.

Take note of the above warning, and add an hosts entry for the CN of the cert if required. Then, retest the controller HTTPS endpoint using curl:

```
curl https://development.lan.mycompany.com
```

And if (and only if) it returns no errors, **install the node software** using the correct CN:

```
 curl https://development.lan.mycompany.com/install | bash 
```

Once the install has finished, you will be given a *claim URL*.

 - For a normal test environment, just paste this into your browser.
 - For a dev / test environment with a NAT network, you will need to alter the host portion of the URL to be `localhost:20443`. 

So, for example, if my *claim URL* was `https://development.lan.mycompany.com/claim/9a7deb0f-b980-11e7-9250-080027e46ee2`, and I'm running a NAT-ed dev environment, I would need to go to this URL in my browser:

https://localhost:20443/claim/9a7deb0f-b980-11e7-9250-080027e46ee2 

Now, we need to:

#### Ingest Storage Node

- Following node installation, go to the *claim URL* provided.
- Select **Claim Node As Normal; It is not a replcement** from the dropdown.
- Hit **Claim Node**.

The controller will attempt to open up a secure communicatiom channel with the node over OpenVPN. When done, you'll see something like this:

![claim_url](https://cloud.swiftstack.com/v1/AUTH_straill/voxygen/claim_node.png)

...hit "Claim Node".

Now we need to add it to our *test* cluster.

- Find your test cluster, and hit **Add Nodes**.
- Find your node in the list - for a dev setup this will be `paco1.swiftstackdev.example.com`.
- Select appropriate region/zone and role settings. For a dev setup this will be **Region 1/Zone 1** and **Swift Node** respectively.
- Hit **Ingest Now**.

When ingest completes, you'll be redirected to the network setup screen. Choose appropriate settings here. For dev, all interfaces should use the IPV4  address `192.168.13.21` as shown below:

![ssc_network](https://cloud.swiftstack.com/v1/AUTH_straill/voxygen/ssc_interfaces.png)

Hit **Reassign Interfaces** and move on to disk setup.

The UI will show you all you unmanaged drives. At this point you can start playing with [Storage Policies](https://www.swiftstack.com/docs/admin/cluster_management/policies.html) if you like; by default, I would just add all disks to the **Standard Replica** storage policy, which creates three copies of each object you upload to Swift.

To do this:

 - Select all the storage drives (there is a label - **All Unmanaged Drives** - you can click to do this quickly)
 - Hit **Format**. 
 - Once drives fomat has completed, select all formatted ("Swift") drives by clicking **All Drives**.
 - Click **Add or Remove Policies**.
 - In the modal, check **Standard Replica** and **Account and Container** and hit **Add Policies**.

Once polices are added, you should see something like this:

![storage_policies](https://cloud.swiftstack.com/v1/AUTH_straill/voxygen/storage_policies.png)

- Click **Enable** on the left nav bar, the **Enable Node**. 
- Click **Click here to deploy**

We're now ready to deploy config to the cluster. All being well, you should see your config changes queued up and ready to go - like the below:

![config_deploy](https://cloud.swiftstack.com/v1/AUTH_straill/voxygen/config_deploy.png)

Hit **Deploy Config to Swift Nodes**.

After the deployment has finished - and if all went well - you'll end up with this screen:

![complete](https://cloud.swiftstack.com/v1/AUTH_straill/voxygen/complete.png)

You're done! Now...

**Snapshot your controller and Storage Node**!!!

...as these will provide the entry point to any development work you might want to do; when you get in trouble, or want to zero things out, revert to these snapshots.

### Endpoints... and Testing

At this point, you'll have a SwiftStack controller, and Swift storage node, that you should be able to run tests against (until you hit your - low - storage limit, anyway).

Your endpoints, from the point of view of your laptop, are now as follows...

- Swift API (Auth v1) - http://localhost:2180/auth/v1.0
- Swift API (Auth v2) - http://localhost:2180/auth/v2.0
- SwiftStack Controller API: https://localhost:20443/api/v1
- SwiftStack Controller Web UI: https://localhost:20443

...To try out the storage API then, let's use cURL:

```
$ curl -i -X GET -H 'x-auth-user: swift' -H 'x-auth-key: supersecretsquirrel' http://localhost:2180/auth/v1.0
HTTP/1.1 200 OK
X-Storage-Url: http://localhost:2180/v1/AUTH_swift
X-Auth-Token: AUTH_tkb642a72b6ef8484fb05400efb12bcdbf
Content-Type: text/plain; charset=UTF-8
Set-Cookie: X-Auth-Token=AUTH_tkb642a72b6ef8484fb05400efb12bcdbf; Path=/
X-Storage-Token: AUTH_tkb642a72b6ef8484fb05400efb12bcdbf
Content-Length: 0
X-Trans-Id: tx9f1e8180055749eb85a6d-0059f08e57
X-Openstack-Request-Id: tx9f1e8180055749eb85a6d-0059f08e57
Date: Wed, 25 Oct 2017 13:15:04 GMT
```

...looks good. 

## Next Steps

At this point, you may want to create some VM templates from the machines you've created, so other people within your organisation can use them - *without* having to go through this install guide! 

Apart from that, where you go next depends entirely on what you would like to do with your dev setup.

 - If you're developing an application that uses Swift, I'd start with the [SwiftStack Docs](https://www.swiftstack.com/docs/) and the [Openstack Swift API Reference](https://docs.openstack.org/swift/latest/api/object_api_v1_overview.html).
 - If you're just trying to play with SwiftStack and are looking for storage clients, we'd probably suggest one of...
   - Our own [SwiftStack Client](https://www.swiftstack.com/downloads)
   - [Python-SwiftClient](https://docs.openstack.org/python-swiftclient/latest/) - the official OpenStack swift python API and CLI client;
   - cURL (of course)  - what you're been using through this doc.

  - Finally, if you'd like to try developing Swift middleare to alter the behaviour of your Swift cluster, you may want to start with [our own example - FooAppenderMiddleware](https://github.com/swiftstack/fooappender_middleware).

Thanks!




---
straill (SwiftStack) - October 2017





