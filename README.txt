ECE 4564 Network Application Design
Team 14: Patrick Kloby, Collin Choy, Andrew Shivers, Tony Tran
Assignment 2: Little Brother
-----------------------------------------------------------------------------------
Files contained:
pistatsd.py
pistatsd_bu.py
readProc.py
pistatsview.py
-----------------------------------------------------------------------------------
Libraries used:
time
json
argparse
pika
sys
pymongo
-----------------------------------------------------------------------------------

The following are the parameters for the host command line
pistatsd –b message broker [–p virtual host] [–c login:password] –k routing key

-b
This is the IP address or named address of the message broker
to connect to
-p
This is the virtual host to connect to on the message broker. If not
specified, should default to the root virtual host (i.e. ‘/’)
-c
Use the given credentials when connecting to the message
broker. If not specified, should default to a guest login.
-k
The routing key to use when publishing messages to the
message broker


For each message the stats client recieves it will print the following:
- current utilization values for each category to stdout
- the highest value observed for each category to stdout
- the lowest value observed for each category to stdout