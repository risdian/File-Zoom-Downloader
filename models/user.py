class User:
    def __init__(self, id, first_name, last_name, display_name, email, user_type, timezone, verified, created_at, last_login_time, status, deleted):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.display_name = display_name
        self.email = email
        self.type = user_type
        self.timezone = timezone
        self.verified = verified
        self.created_at = created_at
        self.last_login_time = last_login_time
        self.status = status
        self.deleted = deleted
    def __repr__(self):
        return f"User({self.id}, { self.display_name },{self.email},)"
