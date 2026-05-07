from typing import Any, Optional


class RBNode:
    def __init__(self, val: Any = None):
        self.val: Any = val
        self.red: bool = False
        self.left: Optional["RBNode"] = None
        self.right: Optional["RBNode"] = None
        self.parent: Optional["RBNode"] = None


class RBTree:
    def __init__(self):
        self.NIL = RBNode()
        self.root: RBNode = self.NIL

    def insert(self, val) -> None:
        node = RBNode(val)
        node.red = True
        node.left = self.NIL
        node.right = self.NIL

        parent: Optional[RBNode] = None
        current = self.root
        while current is not self.NIL:
            parent = current
            if node.val < current.val:
                assert current.left is not None
                current = current.left
            elif node.val > current.val:
                assert current.right is not None
                current = current.right
            else:
                return

        node.parent = parent
        if parent is None:
            self.root = node
        elif node.val < parent.val:
            parent.left = node
        else:
            parent.right = node

        self._fix_insert(node)

    def _fix_insert(self, node: RBNode) -> None:
        while node.parent is not None and node.parent.red:
            p = node.parent
            gp = p.parent
            assert gp is not None

            if p is gp.left:
                uncle = gp.right
                if uncle is not None and uncle.red:
                    p.red = False
                    uncle.red = False
                    gp.red = True
                    node = gp
                else:
                    if node is p.right:
                        node = p
                        self._rotate_left(node)
                        p = node.parent
                        assert p is not None
                        gp = p.parent
                        assert gp is not None
                    p.red = False
                    gp.red = True
                    self._rotate_right(gp)
            else:
                uncle = gp.left
                if uncle is not None and uncle.red:
                    p.red = False
                    uncle.red = False
                    gp.red = True
                    node = gp
                else:
                    if node is p.left:
                        node = p
                        self._rotate_right(node)
                        p = node.parent
                        assert p is not None
                        gp = p.parent
                        assert gp is not None
                    p.red = False
                    gp.red = True
                    self._rotate_left(gp)
        self.root.red = False

    def _rotate_left(self, x: RBNode) -> None:
        y = x.right
        assert y is not None
        x.right = y.left
        if y.left is not None and y.left is not self.NIL:
            y.left.parent = x
        y.parent = x.parent
        if x.parent is None:
            self.root = y
        elif x is x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y
        y.left = x
        x.parent = y

    def _rotate_right(self, x: RBNode) -> None:
        y = x.left
        assert y is not None
        x.left = y.right
        if y.right is not None and y.right is not self.NIL:
            y.right.parent = x
        y.parent = x.parent
        if x.parent is None:
            self.root = y
        elif x is x.parent.right:
            x.parent.right = y
        else:
            x.parent.left = y
        y.right = x
        x.parent = y
