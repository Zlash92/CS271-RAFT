
AWS_INSTANCE_0 = '52.37.112.251'
AWS_INSTANCE_1 = '52.40.128.229'
AWS_INSTANCE_2 = '52.41.5.151'

instances_list = ['52.37.112.251',
                  '52.40.128.229',
                  '52.41.5.151',
                  '52.40.194.211',
                  '52.27.2.226'
                  ]

port = 2000

addr_to_id = {(AWS_INSTANCE_0, port): 0, (AWS_INSTANCE_1, port): 1, (AWS_INSTANCE_2, port): 2}
id_to_addr = {0: (AWS_INSTANCE_0, port), 1: (AWS_INSTANCE_1, port), 2: (AWS_INSTANCE_2, port)}
host_to_id = {AWS_INSTANCE_0: 0, AWS_INSTANCE_1: 1, AWS_INSTANCE_2: 2}
id_to_host = {0: AWS_INSTANCE_0, 1: AWS_INSTANCE_1, 2: AWS_INSTANCE_2}


def add_aws_instance(host, id):
    addr = (host, port)
    addr_to_id[addr] = id
    id_to_addr[id] = addr
    host_to_id[host] = id
    id_to_host[id] = host


def add_all_instances():
    for i in range(len(instances_list)):
        add_aws_instance(instances_list[i], i)

add_all_instances()


