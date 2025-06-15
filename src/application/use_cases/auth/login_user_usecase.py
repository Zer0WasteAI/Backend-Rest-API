class LoginUserUseCase:
    def __init__(self, email_use_case, google_use_case, facebook_use_case, apple_use_case):
        self.email_use_case = email_use_case
        self.google_use_case = google_use_case
        self.facebook_use_case = facebook_use_case
        self.apple_use_case = apple_use_case

    def execute(self, login_type: str, data: dict):
        if login_type == "email":
            return self.email_use_case.execute(data["email"], data["password"])
        elif login_type == "google":
            return self.google_use_case.execute(data["code"])
        elif login_type == "facebook":
            return self.facebook_use_case.execute(data["code"])
        elif login_type == "apple":
            return self.apple_use_case.execute(data["code"])
        else:
            raise Exception("Login type not supported")