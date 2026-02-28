import os

def insecure_function():
    # Hardcoded password
    password = "admin_password_123"
    
    # Dangerous eval usage
    user_input = "os.system('rm -rf /')"
    eval(user_input)
    
    # Shell injection risk
    cmd = "ls " + user_input
    os.system(cmd)
    
    return True
