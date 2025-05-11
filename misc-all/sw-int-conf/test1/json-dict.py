router_data = {
    "routers": [
        {
            "name": "Router1",
            "host": "10.2.205.110",
            "username": "netg",
            "password": "netg",
            "secret": "netg",
            "loopbacks": [
                {
                    "id": 1,
                    "ip": "10.1.1.1",
                    "mask": "255.255.255.255"
                }
            ]
        },
        {
            "name": "Router2",
            "host": "10.2.205.111",
            "username": "netg",
            "password": "netg",
            "secret": "netg",
            "loopbacks": [
                {
                    "id": 1,
                    "ip": "10.1.1.2",
                    "mask": "255.255.255.255"
                },
                {
                    "id": 2,
                    "ip": "10.1.1.5",
                    "mask": "255.255.255.255"
                }
            ]
        },
            
        {
            "name": "Router3",
            "host": "10.2.205.112",
            "username": "netg",
            "password": "netg",
            "secret": "netg",
            "loopbacks": [
                {
                    "id": 1,
                    "ip": "10.1.1.6",
                    "mask": "255.255.255.255"
                }
            ]
        }
    ]
}

# print(abc)

# Iterate over each router in YAML data
for router in router_data['routers']:
    # Render configuration for each router
    # config = template.render(routers=[router])
    print(router)
# print(config)    