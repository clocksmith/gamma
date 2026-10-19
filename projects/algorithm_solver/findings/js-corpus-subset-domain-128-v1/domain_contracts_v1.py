"""Published-domain classification only; no expected values or verdicts enter."""
import math
import string


def reasons(problem_id, args):
    if type(args) is not list:
        return ['arguments_not_list']
    arity={60:2,65:1,74:2,81:2,87:2}
    if problem_id not in arity:raise ValueError('Unreviewed domain')
    if len(args)!=arity[problem_id]:return ['wrong_arity']
    result=[]
    integer=lambda v:type(v) is int
    if problem_id==60:
        n,k=args
        if not integer(n) or not 1<=n<=9:result.append('n_not_integer_in_1_to_9')
        if not integer(k):result.append('k_not_integer')
        elif integer(n) and 1<=n<=9 and not 1<=k<=math.factorial(n):result.append('k_outside_1_to_n_factorial')
    elif problem_id==65:
        s=args[0]
        if type(s) is not str:return ['s_not_string']
        if not 1<=len(s)<=20:result.append('string_length_outside_1_to_20')
        if any(c not in string.ascii_letters+string.digits+'+-.' for c in s):result.append('character_outside_declared_alphabet')
    elif problem_id==74:
        matrix,target=args
        if not integer(target) or not -10000<=target<=10000:result.append('target_outside_integer_bounds')
        if type(matrix) is not list or not 1<=len(matrix)<=100:return result+['row_count_outside_1_to_100']
        if any(type(row) is not list for row in matrix):return result+['row_not_list']
        width=len(matrix[0])
        if not 1<=width<=100:result.append('column_count_outside_1_to_100')
        if any(len(row)!=width for row in matrix):return result+['ragged_matrix']
        if any(not integer(v) or not -10000<=v<=10000 for row in matrix for v in row):return result+['matrix_value_outside_integer_bounds']
        if any(row[i]>row[i+1] for row in matrix for i in range(len(row)-1)):result.append('row_not_nondecreasing')
        if width and any(matrix[i][0]<=matrix[i-1][-1] for i in range(1,len(matrix))):result.append('row_boundary_not_strictly_increasing')
    elif problem_id==81:
        nums,target=args
        if not integer(target) or not -10000<=target<=10000:result.append('target_outside_integer_bounds')
        if type(nums) is not list or not 1<=len(nums)<=5000:return result+['array_length_outside_1_to_5000']
        if any(not integer(v) or not -10000<=v<=10000 for v in nums):return result+['array_value_outside_integer_bounds']
        if sum(nums[i]>nums[(i+1)%len(nums)] for i in range(len(nums)))>1:result.append('not_rotation_of_nondecreasing_sequence')
    else:
        first,second=args
        if type(first) is not str or type(second) is not str:return ['argument_not_string']
        if len(first)!=len(second):result.append('unequal_string_lengths')
        if not 1<=len(first)<=30 or not 1<=len(second)<=30:result.append('string_length_outside_1_to_30')
        if any(c not in string.ascii_lowercase for c in first+second):result.append('character_not_lowercase_english')
    return result
