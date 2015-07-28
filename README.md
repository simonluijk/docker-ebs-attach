# ebs-attach

Docker container that attaches an EBS volume to the local EC2 instance. Useful
with CoreOS when you need persistent storage.

Usage:

```
docker run -it --rm justyo/ebs-attach \
--volumeid vol-123123 \
--device /dev/xvdf \
--region eu-west-1 \
--access-key AWS_ACCESS_KEY \
--secret-key AWS_SECRET_KEY
```

Note: if you don't provide an IAM access and secret key, it relies on the EC2
instance possessing an IAM profile with the following privileges:

- ec2:AttachVolume
- ec2:DetachVolume

## Credits

The wonderful [leg100](https://github.com/leg100) created the original version
of ebs-attach.
