class ProfileUser:
    def __init__(self, uid: str, name: str, phone: str, photo_url: str = "", prefs=None):
        if prefs is None:
            prefs = []
        self.uid = uid
        self.name = name
        self.phone = phone
        self.photo_url = photo_url
        self.prefs = prefs

    def __str__(self):
        return f"ProfileUser(uid={self.uid}, name={self.name}, phone={self.phone}, photo_url={self.photo_url}, prefs={self.prefs})"