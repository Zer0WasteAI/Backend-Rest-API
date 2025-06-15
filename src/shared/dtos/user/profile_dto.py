class UpdateProfileDTO:
    def __init__(self, name: str, phone: str, photo_url: str = "", prefs=None):
        if prefs is None:
            prefs = []
        self.name = name
        self.phone = phone
        self.photo_url = photo_url
        self.prefs = prefs

class ProfileResponseDTO:
    def __init__(self, uid: str, name: str, phone: str, photo_url: str = "", prefs=None):
        if prefs is None:
            prefs = []
        self.uid = uid
        self.name = name
        self.phone = phone
        self.photo_url = photo_url
        self.prefs = prefs
