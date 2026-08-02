#include <stdio.h>
#include <stdlib.h>

#include "libnc.h"

NCTensor *nncp_constant_copy(NCTensor *source)
{
    NCTensor *copy = nc_new_tensor_from_tensor_nz(source);

    if (copy == NULL) {
        fprintf(stderr, "nncp_constant_copy: allocation failed\n");
        abort();
    }
    nc_tensor_copy(copy, source);
    nc_free_tensor(source);
    return copy;
}
