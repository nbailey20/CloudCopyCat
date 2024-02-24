def eval_response(func):
    def wrapper(*args, **kwargs):
        print(f"\nTesting function {func.__name__}")
        res = func(*args, **kwargs)
        if res == False:
            print("Test Failed.")
        else:
            print("Test succeeded.")
        return res
    return wrapper