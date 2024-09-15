# list1 = [[70,80,60],["15-7-2024:10:30:54", "16-7-2024:10:30:54", "17-7-2024:10:30:54"]]

# new_device_data = zip(list1[0], list1[1])
# # print(new_device_data)
# new_device_data = list(zip(list1[0], list1[1]))
# print(new_device_data)


# list2 = ["a", "b", "c"]
# list3 = [1,2,3,5]

# list4 = tuple(zip(list2, list3))
# print(list4)

################## write the python code to find the max and min CPU_utilization for a week ####################

# device_list = ["sw1", "sw2", "sw3", "sw4"]

# CPU_utilization = [[70,80,60,20,10,90,30], [60,80,20,10,40,90,30], [10,30,50,70,90,20,80], [50,80,40,60,10,30,90]]

# for dev in device_list:
#     for cpu in CPU_utilization:
#         print(tuple(zip(device_list,CPU_utilization)))


cpu_utilization = [[70,80,60,20,10,90,30],[60,80,20,10,40,90,30], [10,30,50,70,90,20,80]]

device = ["sw1"]
cpu_utilization = [70,80,60,20,10,90,30]
cpu_utilization.sort()
# print(cpu_utilization)

for item in device:
    print("max cpu utilization value", cpu_utilization[0])
    print("min cpu utilization value", cpu_utilization[-1])


#Homework
# find the list of device which is having average cpu_utilization more than 90%









"""
==============Output=============

root@Aadarshg3:~/devnet/autobundle-may# 
root@Aadarshg3:~/devnet/autobundle-may# python3 list6.py 
[(70, '15-7-2024:10:30:54'), (80, '16-7-2024:10:30:54'), (60, '17-7-2024:10:30:54')]
root@Aadarshg3:~/devnet/autobundle-may# 
root@Aadarshg3:~/devnet/autobundle-may# python3 list6_zip_function.py 
[(70, '15-7-2024:10:30:54'), (80, '16-7-2024:10:30:54'), (60, '17-7-2024:10:30:54')]
(('a', 1), ('b', 2), ('c', 3))
root@Aadarshg3:~/devnet/autobundle-may# 


"""    