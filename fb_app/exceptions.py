from django.core.exceptions import ObjectDoesNotExist, ValidationError


class InvalidGroupNameException(Exception):
    def __str__(self):
        return "Invalid Group Name"


class InvalidMemberException(Exception):
    def __init__(self, user_id):
        self.user_id = user_id

    def __str__(self):
        return f"Doesnt find user with id {self.user_id}"


class InvalidGroupException(Exception):
    def __init__(self, group_id):
        self.group_id = group_id

    def __str__(self):
        return f"Doesnt find Group with id {self.group_id}"


class UserNotInGroupException(Exception):
    def __init__(self, user_id):
        self.user_id = user_id

    def __str__(self):
        return f"Didnt find user in this group {self.user_id}"


class UserIsNotAdminException(Exception):
    def __init__(self, user_id):
        self.user_id = user_id

    def __str__(self):
        return f"Given Person is not an admin {self.user_id}"


class InvalidOffSetValueException(Exception):
    def __str__(self):
        return "Off set can't less than zero"


class InvalidLimitSetValueException(Exception):
    def __str__(self):
        return "Limit can't be less than equal to zero"
