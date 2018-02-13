# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest

from cirq.ops import op_tree
from cirq.ops.raw_types import Operation, QubitLoc, Gate


def test_flatten_op_tree():
    operations = [
        Operation(Gate(), [QubitLoc(0, i)])
        for i in range(10)
    ]

    # Empty tree.
    assert list(op_tree.flatten_op_tree([[[]]])) == []

    # Just an item.
    assert list(op_tree.flatten_op_tree(operations[0])) == operations[:1]

    # Flat list.
    assert list(op_tree.flatten_op_tree(operations)) == operations

    # Tree.
    assert list(op_tree.flatten_op_tree((operations[0],
                                         operations[1:5],
                                         operations[5:]))) == operations

    # Bad trees.
    with pytest.raises(TypeError):
        _ = list(op_tree.flatten_op_tree(None))
    with pytest.raises(TypeError):
        _ = list(op_tree.flatten_op_tree(5))
    with pytest.raises(TypeError):
        _ = list(op_tree.flatten_op_tree([operations[0], (4,)]))


def test_freeze_op_tree():
    operations = [
        Operation(Gate(), [QubitLoc(0, i)])
        for i in range(10)
    ]

    # Empty tree.
    assert op_tree.freeze_op_tree([[[]]]) == (((),),)

    # Just an item.
    assert op_tree.freeze_op_tree(operations[0]) == operations[0]

    # Flat list.
    assert op_tree.freeze_op_tree(operations) == tuple(operations)

    # Tree.
    assert (
        op_tree.freeze_op_tree(
            (operations[0], (operations[i] for i in range(1, 5)),
             operations[5:])) ==
        (operations[0], tuple(operations[1:5]), tuple(operations[5:])))

    # Bad trees.
    with pytest.raises(TypeError):
        op_tree.freeze_op_tree(None)
    with pytest.raises(TypeError):
        op_tree.freeze_op_tree(5)
    with pytest.raises(TypeError):
        _ = op_tree.freeze_op_tree([operations[0], (4,)])


def test_transform_bad_tree():
    with pytest.raises(TypeError):
        _ = list(op_tree.transform_op_tree(None))
    with pytest.raises(TypeError):
        _ = list(op_tree.transform_op_tree(5))
    with pytest.raises(TypeError):
        _ = list(op_tree.flatten_op_tree(op_tree.transform_op_tree([
            Operation(Gate(), [QubitLoc(0, 0)]), (4,)
        ])))


def test_transform_leaves():
    gs = [Gate() for _ in range(10)]
    operations = [
        Operation(gs[i], [QubitLoc(2 * i, i)])
        for i in range(10)
    ]
    expected = [
        Operation(gs[i], [QubitLoc(2 * i + 1, i)])
        for i in range(10)
    ]

    def move_left(op):
        return Operation(op.gate,
                         [QubitLoc(q.x + 1, q.y) for q in op.qubits])

    def move_tree_left_freeze(root):
        return op_tree.freeze_op_tree(
            op_tree.transform_op_tree(root, move_left))

    # Empty tree.
    assert move_tree_left_freeze([[[]]]) == (((),),)

    # Just an item.
    assert move_tree_left_freeze(operations[0]) == expected[0]

    # Flat list.
    assert move_tree_left_freeze(operations) == tuple(expected)

    # Tree.
    assert (
        move_tree_left_freeze(
            (operations[0], operations[1:5], operations[5:])) ==
        (expected[0], tuple(expected[1:5]), tuple(expected[5:])))


def test_transform_internal_nodes():
    operations = [
        Operation(Gate(), [QubitLoc(2 * i, i)])
        for i in range(10)
    ]

    def skip_first(op):
        first = True
        for item in op:
            if not first:
                yield item
            first = False

    def skip_tree_freeze(root):
        return op_tree.freeze_op_tree(
            op_tree.transform_op_tree(root, iter_transformation=skip_first))

    # Empty tree.
    assert skip_tree_freeze([[[]]]) == ()
    assert skip_tree_freeze([[[]], [[], []]]) == (((),),)

    # Just an item.
    assert skip_tree_freeze(operations[0]) == operations[0]

    # Flat list.
    assert skip_tree_freeze(operations) == tuple(operations[1:])

    # Tree.
    assert (
        skip_tree_freeze((operations[1:5], operations[0], operations[5:])) ==
        (operations[0], tuple(operations[6:])))