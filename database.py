import json

class BotDB:
    def __init__(self):
        self.file = "system_data.json"
        try:
            with open(self.file, "r") as f: self.data = json.load(f)
        except:
            self.data = {"locked": False, "users": {}, "total_ops": 0}

    def save(self):
        with open(self.file, "w") as f: json.dump(self.data, f)

    def get_user(self, uid):
        uid = str(uid)
        if uid not in self.data["users"]:
            self.data["users"][uid] = {"lang": "en", "is_auth": False}
            self.save()
        return self.data["users"][uid]

    def set_lang(self, uid, lang):
        self.get_user(uid)["lang"] = lang
        self.save()
