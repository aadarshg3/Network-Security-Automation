def shout(text):
    return text.upper()


def greet_decorator(func):
    def wrapper():
        result = func()
        return f"Modified: {result}"
    return wrapper

def say_hello():
    return "Hello World!"

decorated = greet_decorator(say_hello)
print(decorated())