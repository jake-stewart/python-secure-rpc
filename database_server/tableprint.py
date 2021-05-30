BORDER_STYLES = [
    [" ", " "],
    ["─", "│"],
    ["━", "┃"],
    ["═", "║"],
    ["-", "|"],
    ["─", "│"],
    ["╌", "┆"],
    ["╍", "┇"],
    ["▀", "█"],
    ["═", "│"],
    ["─", "║"],
]

CORNER_STYLES = [
    [" ", " ", " ", " ", " ", " ", " ", " ", " "],
    ["┌", "┐", "└", "┘", "├", "┤", "┬", "┴", "┼"],
    ["┏", "┓", "┗", "┛", "┣", "┫", "┳", "┻", "╋"],
    ["╔", "╗", "╚", "╝", "╠", "╣", "╦", "╩", "╬"],
    ["+", "+", "+", "+", "+", "+", "+", "+", "+"],
    ["╭", "╮", "╰", "╯", "├", "┤", "┬", "┴", "┼"],
    ["┌", "┐", "└", "┘", "├", "┤", "┬", "┴", "┼"],
    ["┏", "┓", "┗", "┛", "┣", "┫", "┳", "┻", "╋"],
    ["█", "█", "▀", "▀", "█", "█", "█", "▀", "█"],
    ["╒", "╕", "╘", "╛", "╞", "╡", "╤", "╧", "╪"],
    ["╓", "╖", "╙", "╜", "╟", "╢", "╥", "╨", "╫"],
]


def right_pad_string(string, width):
    padding = (width - len(string)) * " "
    return padding + " " + string + " "

def left_pad_string(string, width):
    padding = (width - len(string)) * " "
    return " " + string + " " + padding

def print_table(data, alignments=None, border_style=4, corner_style=None):
    headings = data[0].keys()

    # convert the values of each field to strings in
    # respective lists based on the key
    content_arrays = []
    for i, heading in enumerate(headings):
        content_arrays.append([])
        for row in data:
            content_arrays[i].append(str(row[heading]))

    if not alignments:
        alignments = ["l" for key in range(len(headings))]

    if not corner_style:
        corner_style = border_style

    border_style = BORDER_STYLES[border_style]
    corner_style = CORNER_STYLES[corner_style]

    column_widths = []

    top_border = corner_style[0]
    bottom_border = corner_style[2]
    row_separator = corner_style[4]
    current_row = border_style[1]

    for array, heading in zip(content_arrays, headings):

        # calculate column size
        largest_element = max(array, key=lambda x: len(x))
        column_width = max(len(largest_element), len(heading))
        column_widths.append(column_width)

        current_row += left_pad_string(heading, column_width) + border_style[1]

        # generate heading row and row separator with newly found width
        row_separator += (column_width + 2) * border_style[0] + corner_style[8]
        top_border += (column_width + 2) * border_style[0] + corner_style[6]
        bottom_border += (column_width + 2) * border_style[0] + corner_style[7]

    row_separator = row_separator[:-1] + corner_style[5]
    bottom_border = bottom_border[:-1] + corner_style[3]
    top_border = top_border[:-1] + corner_style[1]

    # print headings/separators
    print(top_border)
    print(current_row)
    print(row_separator)

    # print each row of contents
    for row in zip(*content_arrays):
        current_row = border_style[1]
        for val, alignment, width in zip(row, alignments, column_widths):
            if alignment == "l":
                current_row += left_pad_string(val, width)
            else:
                current_row += right_pad_string(val, width)

            current_row += border_style[1]
        print(current_row)

    # print final row separator
    print(bottom_border)
