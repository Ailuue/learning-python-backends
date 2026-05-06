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
                
    def delete(self, val):
        if self.val is None:
            return self
        if val < self.val:
            if self.left is not None:
                self.left = self.left.delete(val)
        elif val > self.val:
            if self.right is not None:
                self.right = self.right.delete(val)
        else:
            if self.left is None:
                return self.right
            elif self.right is None:
                return self.left
            min_larger_node = self.right
            while min_larger_node.left is not None:
                min_larger_node = min_larger_node.left
            self.val = min_larger_node.val
            self.right = self.right.delete(min_larger_node.val)
        return self
    
    def preorder(self, visited):
        if self.val:
            visited.append(self.val)
        if self.left:
            self.left.preorder(visited)
        if self.right:
            self.right.preorder(visited)
        return visited
    
    def postorder(self, visited):
        if self.left:
            self.left.postorder(visited)
        if self.right:
            self.right.postorder(visited)
        if self.val:
            visited.append(self.val)
        return visited

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
    
    def exists(self, val):
        if self.val == val:
            return True
        if val < self.val:
            if self.left:
                return self.left.exists(val)
        if val > self.val:
            if self.right:
                return self.right.exists(val)
        return False
    
    def height(self):
        left = 0
        right = 0
        if not self.val:
            return 0
        if self.left:
             left = self.left.height()
        if self.right:
            right = self.right.height()
        return max(left, right) + 1