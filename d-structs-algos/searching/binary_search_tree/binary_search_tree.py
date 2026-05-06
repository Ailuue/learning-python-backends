class binary_search_tree_node:
    def __init__(self, val=None):
        self.val = val
        self.left = None
        self.right = None

    def insert(self, val):
        if self.val is None:
            self.val = val
            return
        if val < self.val:
            if self.left is None:
                self.left = binary_search_tree_node(val)
            else:
                self.left.insert(val)
        else:
            if self.right is None:
                self.right = binary_search_tree_node(val)
            else:
                self.right.insert(val)

    def inorder(self, result=None):
        if result is None:
            result = []
        if self.left:
            self.left.inorder(result)
        if self.val is not None:
            result.append(self.val)
        if self.right:
            self.right.inorder(result)
        return result