""" 

#=====================================================
# Class-project-1
# Parsing of a given string second logic
#=====================================================

raw_data = "T6h32i%&s&8i^s9(I534n250d$i65a"

formatted_data = ""

for char in raw_data:
    if char.isalpha():
        formatted_data += char
print(formatted_data)        





#=====================================================
                    # output
#=====================================================

root@Aadarshg3:~/devnet/autobundle-may# python3 parsing_str4.py 
ThisisIndia
root@Aadarshg3:~/devnet/autobundle-may#
#=====================================================

"""
""" 
# String is immutable because we can't change a value in a string.
# while List is mutable

>>> device_list = ["R1" , "R2" , "R3"]
>>> device_list[1]
'R2'
>>> device_list[2]
'R3'
>>> device_list[0]
'R1'
>>> 
>>> 
>>> device_list[0] = "R0"
>>> device_list
['R0', 'R2', 'R3']
>>> 


 """

# #=====================================================
# # Class-project-1
# # Parsing of a given string second logic
# #=====================================================

# raw_data = "T6h32i%&s&8i^s9(I534n250d$i65a"

# formatted_data = ""

# for char in raw_data:
#     if char.isalpha():
#         formatted_data += char
# print(formatted_data)        



















""" 
#=========== Parsing of a given String==============

str1 = "I^!@#&n^@!&d@!#^$i#*&a"

# create an empty container ("formatted_str") who holds apha values as an string

formatted_str = ""

# now apply for loop becuase it is finite loop and then apply condition if char is alpha then save that char in formatted str
for char in str1:
    if char.isalpha():
        # formatted_str = formatted_str + char
        formatted_str += char
print(formatted_str)    

 """





    
   
""" 

"""