
def session(a, b, c, *vargs, host='10.1.1.1', port=80, timeout=60, source_address='100.1.1.1', **kwargs):
    print(a, b, c)
    print(vargs)
    print(host, port, timeout, source_address)
    print(kwargs)

session(10, 20, 30, 4, 5, 6, host='10.1.1.1', port=80, timeout=60, source_address='100.1.1.1',test1="testing1", test2="testing2", test3="testing3" )







# # defining function
# def connect(host=None, port=443, timeout=30, source_address=None):
#     print(host, port, timeout, source_address)

# # calling function
# # connect(host='10.1.1.1', port=80, timeout=60, source_address='100.1.1.1')
# connect()



# def session(**kwargs):
#     print(kwargs)

# session(test1="testing1", test2="testing2", test3="testing3") # variable key-word arguments

# def session(host='10.1.1.1', port=80, timeout=60, source_address='100.1.1.1', **kwargs):
#     print(host, port, timeout, source_address,kwargs  )
# session(host=None, port=443, timeout=30, source_address=None,test1="testing1", test2="testing2")
