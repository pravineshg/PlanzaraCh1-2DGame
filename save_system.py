import json, os, datetime

SAVE_FILE = "planzara_save.json"

DEFAULT = {
    'chapter':1,'scene':'title','player_pos':[480,400],
    'inventory':[],'missions_done':[],'flags':{},
    'playtime':0.0,'save_time':None,'credits':500,'character':'mits'
}

def save(state:dict)->bool:
    try:
        state['save_time']=datetime.datetime.now().isoformat()
        with open(SAVE_FILE,'w') as f: json.dump(state,f,indent=2)
        return True
    except Exception as e: print(f"Save error: {e}"); return False

def load()->dict|None:
    if not os.path.exists(SAVE_FILE): return None
    try:
        with open(SAVE_FILE,'r') as f: data=json.load(f)
        state=dict(DEFAULT); state.update(data); return state
    except Exception as e: print(f"Load error: {e}"); return None

def has_save()->bool: return os.path.exists(SAVE_FILE)
def delete():
    if os.path.exists(SAVE_FILE): os.remove(SAVE_FILE)
def default()->dict: return dict(DEFAULT)