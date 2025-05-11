
# string.replace(oldvalue, newvalue, count)

raw_data = "T6h32i%&s&8i^s9(I534n250d$i65a"

formatted_data = ""

for char in raw_data:
    if char.isalpha():
        formatted_data += char
# print(formatted_data)  

output = formatted_data.replace("s", "s ")
print(output)



""" 
output
root@Aadarshg3:~/devnet/autobundle-may# python3 str-replace.py 
This is India
root@Aadarshg3:~/devnet/autobundle-may# 
"""



