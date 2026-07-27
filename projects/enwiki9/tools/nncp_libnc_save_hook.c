#define _GNU_SOURCE

#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>

#include "libnc.h"

/*
 * Observation-only LibNC interposer.  When NNCP finishes constructing its
 * parameter list, save the seeded coefficients through LibNC's public API.
 * The hook does not modify any tensor or graph operation.
 */
void nc_param_list_end(NCParamList *param_list)
{
    typedef void (*end_func)(NCParamList *);
    static end_func real_end;
    static int saved;
    const char *path;
    size_t count;

    if (!real_end) {
        real_end = (end_func)dlsym(RTLD_NEXT, "nc_param_list_end");
        if (!real_end) {
            fprintf(stderr, "cannot resolve nc_param_list_end\n");
            abort();
        }
    }
    path = getenv("NNCP_SAVE_COEFS");
    count = nc_get_param_count(param_list);
    if (!saved && path && path[0] != '\0' && count > 0) {
        nc_save_coefs(param_list, path);
        fprintf(stderr, "NNCP_SAVE_COEFS wrote %zu parameters to %s\n",
                count, path);
        saved = 1;
    }
    real_end(param_list);
}
