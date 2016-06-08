README - CS271 Project Part 2 - RAFT

Manu Gopinathan
Morten Flood


To run this project:

1. Server need every source file except client.py in directory to work.

2. In aws_instances input all your desired instances in the instances_list by their IP address. Each instance id will correspond to their index in the list.

3. In aws_instances input your desired port number.

4. Run the server with the argument "server id", which must correspond to the index in the instances_list and must be an int. Example "python server.py 0" to run the server on the instance corresponding to the first instance in the list.

5. Run client from anywhere. Client needs most of the files in directory to work.

6. Client commands:
	- 'lookup' : lookup to leader
	- 'lookup [id]' : lookup to server with same id
	- 'post [msg]' : post msg to leader
	- 'close' : close the client connection

7. Persistance: 
	Every instance saves the state of the server whenever log, term or voted_for is modified as a .pickle-object
	with name 'raft-state-server-[id].pickle'. So server 0 saves an object with name 'raft-state-server-0.pickle'

	To delete log do command 'rm raft-state-server-[id].pickle' in the same directory as the source files on the instance.
