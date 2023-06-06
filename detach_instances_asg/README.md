# detach_instances_asg.py
-----------------

## Script Function
-----------------
This script will detach the specified instance from it's Auto Scaling Group

## Parameters
-----------------
*  -h, --help  ```show this help message and exit```
*  --awskey AWSKEY  ```AWS Access Key ID```
*  --awssecret AWSSECRET ```AWS Secret Key ID```
*  -i INSTANCE, --instance INSTANCE ```Instance to be removed from ASG```


## Calling Script Example
-----------------
usage: detach_instances_asg.py [-h] [--awskey AWSKEY] [--awssecret AWSSECRET] [-i INSTANCES [INSTANCES ...]]

* Remove single instance from it's Auto Scaling Group
```bash
./detach_instances_asg.py --awskey $AWSKEY --awssecret $AWSSECRET -i i-0e9549756596de29f
```