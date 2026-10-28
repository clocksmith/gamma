def gamma_native443(chars):
    length = Solution().compress(chars)
    if type(length) is not int:
        return {'bad_length_type': type(length).__name__}
    return {'length': length, 'prefix': chars[:length]}
