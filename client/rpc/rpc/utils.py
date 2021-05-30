import json

def compact_json(data):
    return json.dumps(
        data,
        separators=(",", ":"),
        indent=None
    )

def func_str(func_name, args, kwargs):
    arg_string = ""
    if args:
        arg_string += ", ".join(map(repr, args))
        if kwargs:
            arg_string += ", "

    if kwargs:
        arg_string += ", ".join(
            key + "=" + repr(val) for key, val in kwargs.items()
        )

    return func_name + "(" + arg_string + ")"
