ip1 = input("Enter your IP address: ")
ip2 = ip1.split(".")
# print(ip2)
# for ele in ip2:
    # print(ele)
if float(ip2[0]) == 10. and float(ip2[0]) >= 0 and float(ip2[0])<=255 and float(ip2[1])>=0 and float(ip2[1]) <= 255 and float(ip2[2]) >= 0 and float(ip2[2]) <=255 and float(ip2[3]) >= 0 and float(ip2[3]) <=255:
    print("Class A Private IP Address")
elif float(ip2[0]) == 172. and float(ip2[1]) >= 16. and float(ip2[1]) <=31. and float(ip2[0]) >= 0 and float(ip2[0])<=255 and float(ip2[1])>=0 and float(ip2[1]) <= 255 and float(ip2[2]) >= 0 and float(ip2[2]) <=255 and float(ip2[3]) >= 0 and float(ip2[3]) <=255: 
    print("Class B Private IP Address")     
elif  float(ip2[0]) == 192. and float(ip2[1]) == 168. and float(ip2[0]) >= 0 and float(ip2[0])<=255 and float(ip2[1])>=0 and float(ip2[1]) <= 255 and float(ip2[2]) >= 0 and float(ip2[2]) <=255 and float(ip2[3]) >= 0 and float(ip2[3]) <=255:    
    print("Class C Private IP Address")
else:
    print("Not a Private IP Address")    
    
print("DONE")    




    
"""
########## OUTPUT #####################

# code that tells if this is a private class of which class

root@Aadarshg3:~/devnet/autobundle-may# python3 list3_modified.py 
Enter your IP address: 192.168.2.2
192
168
2
2
Class C Private IP Address
root@Aadarshg3:~/devnet/autobundle-may# python3 list3_modified.py 
Enter your IP address: 10.1.1.1
Class A Private IP Address
root@Aadarshg3:~/devnet/autobundle-may# python3 list3_modified.py 
Enter your IP address: 10.255.455.1
Not a Private IP Address
root@Aadarshg3:~/devnet/autobundle-may# python3 list3_modified.py 
Enter your IP address: 192.168.2.555
Not a Private IP Address
root@Aadarshg3:~/devnet/autobundle-may# python3 list3_modified.py 
Enter your IP address: 172.16.2.4
Class B Private IP Address
root@Aadarshg3:~/devnet/autobundle-may# python3 list3_modified.py 
Enter your IP address: 172.155.56.555
Not a Private IP Address
root@Aadarshg3:~/devnet/autobundle-may# python3 list3_modified.py 
Enter your IP address: 172.16.233.555
Class B Private IP Address
root@Aadarshg3:~/devnet/autobundle-may# python3 list3_modified.py 
Enter your IP address: 172.16.2.3
Class B Private IP Address
root@Aadarshg3:~/devnet/autobundle-may# python3 list3_modified.py 
Enter your IP address: 172.16.255.255
Class B Private IP Address
root@Aadarshg3:~/devnet/autobundle-may# python3 list3_modified.py 
Enter your IP address: 172.16.255.256
Not a Private IP Address
root@Aadarshg3:~/devnet/autobundle-may# 
root@Aadarshg3:~/devnet/autobundle-may# 
root@Aadarshg3:~/devnet/autobundle-may# 
root@Aadarshg3:~/devnet/autobundle-may# git status
On branch aadarsh
Your branch is up to date with 'origin/aadarsh'.

Changes not staged for commit:
  (use "git add/rm <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
        deleted:    split-join.py

Untracked files:
  (use "git add <file>..." to include in what will be committed)
        list3_modified.py
        private-ip_using-list.py

no changes added to commit (use "git add" and/or "git commit -a")
root@Aadarshg3:~/devnet/autobundle-may# git add list3_modified.py 
root@Aadarshg3:~/devnet/autobundle-may# git commit -m <modified>
bash: syntax error near unexpected token `newline'
root@Aadarshg3:~/devnet/autobundle-may# git push
Everything up-to-date
root@Aadarshg3:~/devnet/autobundle-may# 



"""    
    