class OmetriaMember:
    def __init__(self, id, firstname, lastname, email, status):
        self.id = id
        self.firstname = firstname
        self.lastname = lastname
        self.email = email
        self.status = status

    def to_dict(self):
        return {
            "id": self.id,
            "firstname": self.firstname,
            "lastname": self.lastname,
            "email": self.email,
            "status": self.status
        }
