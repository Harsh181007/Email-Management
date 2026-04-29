REGISTERED_INTERNS = {
    "harshdhimmar111@gmail.com",
    "harshdhimmar1810@gmail.com",
    "harshdhimmar24052004@gmail.com",
    "harshdhimmar999@gmail.com",
    "intern1@company.com",
    "intern2@company.com",
    "intern3@company.com",
    "intern4@company.com",
    "intern5@company.com",
    "intern6@company.com",
    "intern7@company.com"    
}

def is_registered_intern(email: str) -> bool:
    email = email.lower().strip()
    return email in {i.lower().strip() for i in REGISTERED_INTERNS}        