import json

class BotDB:
    def __init__(self):
        self.path = "bot_data.json"
        try:
            with open(self.path, "r") as f: self.data = json.load(f)
        except:
            self.data = {"locked": False, "users": {}, "total_reports": 0}

    def save(self):
        with open(self.path, "w") as f: json.dump(self.data, f)

    def get_lang(self, uid):
        return self.data["users"].get(str(uid), {}).get("lang", "en")

    def set_lang(self, uid, lang):
        if str(uid) not in self.data["users"]: 
            self.data["users"][str(uid)] = {"reports": 0}
        self.data["users"][str(uid)]["lang"] = lang
        self.save()
