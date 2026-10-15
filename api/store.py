import os, json
print("Loading _store.py safe version")
def get_users():
    return {}
def set_users(v):
    print(f"set_users called {len(str(v))} chars")
    return True
def get_pending():
    return {}
def set_pending(v):
    return True
