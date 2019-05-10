# awsddns
A docker file and python script to perform Dynamic DNS with AWS Route53.

# setup

1.  Install Docker
2.  docker build -t awsddns .
3.  docker run -d -i -t --rm --env AWS_ACCESS_KEY_ID=$AWS_ACCES_KEY --env AWS_SECRET_ACCESS_KEY=$AWS_SECRET_KEY awsddns python dns.py --domain $YOUR_DOMAIN --zoneid $ROUTE53_ZONE_ID --interval=300

* Change the interval to check/update to whatever you want (in seconds).


