export NET_USERNAME=netg
export NET_PASSWORD='india'
export NET_ENABLE_SECRET='india'     # if needed
# Optional (SSH key instead of password):
# export NET_SSH_KEYFILE=~/.ssh/id_rsa
python3 main.py


setx NET_USERNAME "netg"
setx NET_PASSWORD "india"
setx NET_ENABLE_SECRET "india"
# setx NET_SSH_KEYFILE "C:\Users\<user>\.ssh\id_rsa"
# Restart shell, then:
python main.py

