import os

def function_with_many_issues(a,b,c,d,e,f,g):
    x=1 # missing whitespace
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        if f > 0: # deep nesting
                            print("Too deep!")
    
    # Very long line that should trigger E501
    very_long_string_variable = "this is a very long string that will definitely exceed the standard eighty character limit of most linting tools used in python development"
    
    return x
