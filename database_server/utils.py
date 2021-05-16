import json
import os

def int_input(prompt):
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Invalid input, try again.\n")

def string_input(prompt, min_length, max_length):
    user_input = input(prompt)
    while not min_length <= len(user_input) <= max_length:
        print(
            "Invalid input. Must be at least", min_length,
            "and at most", max_length, "characters long.\n"
        )
        user_input = input(prompt)
    return user_input


def _clear():
    os.system("clear")

def _cls():
    os.system("cls")

if os.name == "posix":
    clear_screen = _clear
else:
    clear_screen = _cls

