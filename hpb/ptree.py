# from: https://stackoverflow.com/questions/51903172/how-to-display-a-tree-in-python-similar-to-msdos-tree-command
def ptree(start, tree, indent_width=4):
    def _ptree(start, parent, tree, grandpa=None, indent=""):
        if parent != start:
            if grandpa is None:  # Ask grandpa kids!
                print(parent, end="")
            else:
                print(parent)
        if parent not in tree:
            return
        for child in tree[parent][:-1]:
            print(indent + "├" + "─" * indent_width, end="")
            _ptree(start, child, tree, parent, indent + "│" + " " * 4)
        child = tree[parent][-1]
        print(indent + "└" + "─" * indent_width, end="")
        _ptree(start, child, tree, parent, indent + " " * 5)  # 4 -> 5

    parent = start
    print(start)
    _ptree(start, parent, tree)


# if __name__ == "__main__":
#     dct = {
#         -1: [0, 60000],
#         0: [100, 20, 10],
#         100: [30],
#         30: [400, 500],
#         60000: [70, 80, 600],
#         500: [495, 496, 497]
#     }
#     ptree(-1, dct)
