#!/usr/bin/env python3
from copy import copy

import numpy as np


def get_all_isobase(m, n):
    '''
    return all the isobases
    :param m: max number of
    :param n:
    :return:
    '''
    assert n >= m
    generators = []
    for i in range(1, m + 1):
        generators.append(get_isobase(i, n))

    for it in generators:
        for element in it:
            yield element


def get_isobase(m, n):
    '''
    get an isomorphic base for the bipartite graphs set when the biggest set is already labelled.
    :param m: cardinal of the smallest
    :param n:
    :return:
    '''
    assert n >= m
    row, col = 0, 0
    # initialize base matrix to all nan
    base = np.ones((m, n)) * np.nan
    # initialize remaining ones and lines
    rem_1 = n
    rem_r = m
    working = [(base, row, col, rem_1, rem_r)]

    while len(working):
        base, row, col, rem_1, rem_r = working.pop()
        is_triv, solver = is_trivial(base, row, col, rem_1, rem_r)
        if is_triv:
            solver()
            yield copy(base)

        else:
            case0, case1 = split01(base, row, col, rem_1, rem_r)
            if case0 is not None:
                working.append(case0)
            working.append(case1)


def insert_zero(sub_base, row, col, rem_1, rem_r):
    '''
    just add a zero and move the custor to the next location
    '''

    if is_out_of_the_table(sub_base, row, col, rem_1, rem_r):
        return row, col, rem_1, rem_r

    sub_base[row, col] = 0
    row, col, _, rem_r = get_next_cursor_pos(sub_base, row, col, rem_1, rem_r)
    return row, col, rem_1, rem_r


def insert_one(sub_base, row, col, rem_1, rem_r):
    '''
    initialize a new column, by putting a 1 in the top left corner and zeros above
    '''

    if is_out_of_the_table(sub_base, row, col, rem_1, rem_r):
        return row, col, rem_1, rem_r

    sub_base[row:, col] = 0
    sub_base[row, col] = 1
    row, col, _, rem_r = get_next_cursor_pos(sub_base, row, col, rem_1, rem_r)
    return row, col, rem_1 - 1, rem_r


def is_out_of_the_table(sub_base, row, col, rem_1, rem_r):
    if row == -1 or col == -1:
        return True
    else:
        return False


def get_next_cursor_pos(sub_base, row, col, rem_1, rem_r):
    '''
    move the cursor to the next position after an operation
    '''

    if is_out_of_the_table(sub_base, row, col, rem_1, rem_r):
        return row, col, rem_1, rem_r

    if sub_base.shape[1] > col + 1:  # move righ
        return row, col + 1, rem_1, rem_r
    else:
        # move 1 row down, find the first column with nan element
        if not is_finished(sub_base, row, col, rem_1, rem_r):
            row += 1
            fcn = next((i for i, v in enumerate(np.isnan(sub_base[row])) if v))

            return row, fcn, rem_1, rem_r - 1
        # all over
        else:
            row, col = sub_base.shape
            return -1, -1, 0, 0


def pad_lines_with_zeros(sub_base, row, col, rem_1, rem_r):
    '''
    add zeros until the line is finished and return the cursor on the next line
    '''

    if is_out_of_the_table(sub_base, row, col, rem_1, rem_r):
        return row, col, rem_1, rem_r

    sub_base[row][col:] = 0
    row, col, _, rem_r = get_next_cursor_pos(sub_base, row, sub_base.shape[1] - 1, rem_1, rem_r)
    return row, col, rem_1, rem_r


def fill_remaining_with_eye(sub_base, row, col, rem_1, rem_r):
    assert is_trivial(sub_base, row, col, rem_1, rem_r)
    while not is_finished(sub_base, row, col, rem_1, rem_r):
        # print("-------------\n%s\n------------\n"%sub_base)
        row, col, rem_1, rem_r = insert_one(sub_base, row, col, rem_1, rem_r)
        # print("-------------\n%s\n------------\n" % sub_base)
        row, col, rem_1, rem_r = pad_lines_with_zeros(sub_base, row, col, rem_1, rem_r)


def split01(base, row, col, rem_1, rem_r):
    '''
    return a tuple containing the two possible choices if it's possible or just one if it's the first 1 in the line
    '''
    if np.any(base[row] == 1):
        b0 = copy(base)
        row_0, col_0, rem_1_0, rem_r_0 = insert_zero(b0, row, col, rem_1, rem_r)
        case0 = b0, row_0, col_0, rem_1_0, rem_r_0
    else:
        case0 = None
    b1 = copy(base)
    row_1, col_1, rem_1_1, rem_r_1 = insert_one(b1, row, col, rem_1, rem_r)
    case1 = b1, row_1, col_1, rem_1_1, rem_r_1
    return (case0, case1)


def is_trivial(base, row, col, rem_1, rem_r):
    '''
    tell if a matrix can be trivially solved, that is we know for sure where to put the ones.
    @return a tuple containing True|False for triviality and the function to solve the problem if possible
    '''
    remaining_ones = base.shape[1] - np.sum(base == 1)
    remaining_lines = np.sum(np.all(base != 1, axis=1))
    assert not remaining_lines > remaining_ones  # should not happen, ones starvationw
    # solve it with eye when the number of line is equal to the number of ones
    if remaining_ones == remaining_lines:
        def fill_remaining_with_eye_():
            # if there's already a one on the current line, we need to pad
            if any(base[row] == 1):
                row_t, col_t, rem_1_t, rem_r_t = pad_lines_with_zeros(base, row, col, rem_1, rem_r)
            else:  # we are at the begining of a new line, no need to pad
                row_t, col_t, rem_1_t, rem_r_t = row, col, rem_1, rem_r
            return fill_remaining_with_eye(base, row_t, col_t, rem_1_t, rem_r_t)

        return (True, fill_remaining_with_eye_)
    # trivial if only 1 line left with nans, then we fill it with ones
    elif np.sum(np.any(np.isnan(base), axis=1)) == 1:
        def fill_remaining_with_ones_():
            return fill_remaining_with_ones(base, row, col, rem_1, rem_r)

        return (True, fill_remaining_with_ones_)
    else:
        return (False, None)


def fill_remaining_with_ones(base, row, col, rem_1, rem_r):
    base[-1][col:] = 1
    row, col = base.shape
    return row, col, 0, 0


def is_finished(base, row, col, rem_1, rem_r):
    '''
    tell you if the matrix can be used to generate graph
    '''
    return not np.any(np.isnan(base))
