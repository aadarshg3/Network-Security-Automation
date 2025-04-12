import time

def log_and_timer(func):
    def wrapper(*args, **kwargs):
        ip = args[0]           # assume first arg is IP
        command = args[1]      # assume second arg is command
        print(f"📡 Sending command to {ip}: {command}")

        start = time.time()    # start timer
        result = func(*args, **kwargs)  # call the original function
        end = time.time()      # end timer

        print(f"⏱️ Time taken: {end - start:.2f} seconds")
        return result
    return wrapper

@log_and_timer
def send_command(ip, command):
    time.sleep(2)  # Simulating a 2-second command execution
    return f"✅ Output: '{command}' from device {ip}"
