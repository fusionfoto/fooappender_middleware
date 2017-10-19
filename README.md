SwiftStack Custom Middleware Example: FooAppender
=================================================

This repo is intended to present an as-simple-as-usefully-possible example of writing, and using, custom middleware in SwiftStack using an on-premise Controller.

What does it do?
================
This middleware ensures, usefully, that a user metadata value of foo:$bar (where $bar can be configured) exists on objects you upload or modify in your SwiftStack cluster. 

To restrict this behaviour to certain accounts, containers, or objects, you can configure an `enforce_pattern` - only objects whose full name (`Account`/`Container`/`Object`) matches this pattern will be modified by this middleware.

How do I deploy it?
===================
The easiest way to deploy this is to copy `__init.py__` to `/opt/ss/lib/python2.7/site-packages/fooappender_middleware/__init__.py` on *every* Swift node running proxy services in your cluster. The `fooappender_middleware`, and its content, should be owned by root.

To do this quickly, log in as root, and clone this repo:

```
  # cd /opt/ss/lib/python2.7/site-packages && git clone https://github.com/swiftstack/fooappender_middleware.git
```
 
### Enable custom middleware on your SwiftStack Controller
As root, login to the controller over ssh, become root, and execute the below if you have not already to enable the **Custom Middleware** feature:
```
# . /opt/ss/etc/profile.d/01-swiftstack-controller.sh
# m feature add custom_middleware localadmin
```
Then, on your "Middleware" page, hit "Add Custom Middleware", and set 
 
  - **name** to "fooappender_middleware"
  - **config** to the below:

```
paste.filter_factory = fooappender_middleware:my_filter_factory
enforce_pattern      = ^[^/]+/[^/]+_fooenforce/
bar                  = Bar
```

> #### Configuring things...
> * The 'bar' variable alters the value set for your `foo` metadata key.
> * The `enforce_pattern` variable controls which object paths will modified by this middleware. The regex is tested against the full name of your object - `Account`/`Container`/`Object`.
> * With the example above, objects in any container whose name ends in `_fooenforce` will have the `foo` metadata keyval appended to them.

Save your changes. Then, add the middleware to the Swift middleware pipeline:

 - Hit **View Pipeline Placement**.
 - Drag the `fooappender_middleware` middleare to the end of the proxy pipeline;
 - Click **Save and Validate Pipeline**;
 - Hit **Click here to deploy**;
 - Hit **Deploy Config to Swift Nodes**.

Once the config deploy has finished, restart the proxy processes:
 - **Clusters** > `Your Cluster` > **Manage** > **Restart Proxy Services on Swift Nodes**.

How do I use it once it's deployed?
==================
First, create a container within your account such that "`Account`/`Container`" matches the `enforce_pattern` config setting above.

If you've followed the above instuctions, this means you could create a container named `container_fooenforce` within your account, for example.

Then, either PUT or POST an object within it.

All being well, you should find it has a user metadata value of `foo`:`Bar` appended to it without interaction on your part.

Iterating and fixing problems
=============================
The most common symptom of a problem is that you become unable to connect to the Swift API. This would occur, for example, if your middleware throws an exception on load.

To find the exception (and to fix it), log into your proxy as root, tail -f the syslog to see the ssswift-proxy service logs (on EL this would be accomplished via `journalctl -f`; on Ubuntu, I suspect `tail -f /var/log/syslog` is your friend here) - and look for the inevitable exception the Swift proxy service has thrown when trying to load the middleware.

Fix the exception in your `__init__.py`, then restart the proxy service to try again.


