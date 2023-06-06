# resize_instance.py
-----------------

## Script Function
-----------------

The purpose of this script is to facilitate resizing of instances programmatically on AWS. This script is used to adjust the size of a specific EC2 instance without needing to manually stop and start the instance through the AWS Management Console.

## Parameters
-----------------
*  --awskey AWSKEY `AWS Access Key ID`
*  --awssecret AWSSECRET `AWS Secret Key ID`
*  -i INSTANCE, --instance INSTANCE `Instance ID of node that is being resized`
*  -s SIZE, --size SIZE `Size of instance that it is being resized to`

## Calling Script Example
-----------------
usage: resize_instance.py [-h] --awskey AWSKEY --awssecret AWSSECRET -i INSTANCE -s SIZE

```bash
./resize_instance.py --awskey $AWSKEY --awssecret $AWSSECRET \
                     -i $INSTANCE_ID \
                     -s $NEW_SIZE
```

Please remember to replace `$AWSKEY`, `$AWSSECRET`, `$INSTANCE_ID`, and `$NEW_SIZE` with your actual values when running the script.
