#define _GNU_SOURCE

#include <dlfcn.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>

#include "libnc.h"

/*
 * Observation-only LibNC interposer for miniature online-update parity.
 * It retains the first completed parameter list, saves its initial values, and
 * saves the values immediately after each optimizer update. It never mutates a
 * tensor, graph, optimizer state, or update schedule.
 */
static NCParamList *observed_param_list;
static uint64_t observed_update_count;

static const char *output_directory(void)
{
    const char *path = getenv("NNCP_UPDATE_TRACE_DIR");
    if (!path || path[0] == '\0')
        return NULL;
    return path;
}

static void save_snapshot(const char *kind, uint64_t index)
{
    const char *directory = output_directory();
    char path[4096];
    int count;

    if (!directory || !observed_param_list)
        return;
    count = snprintf(path, sizeof(path), "%s/%s_%06" PRIu64 ".coefs",
                     directory, kind, index);
    if (count < 0 || (size_t)count >= sizeof(path)) {
        fprintf(stderr, "NNCP update snapshot path is too long\n");
        abort();
    }
    nc_save_coefs(observed_param_list, path);
    fprintf(stderr, "NNCP_UPDATE_TRACE wrote %s\n", path);
}

void nc_param_list_end(NCParamList *param_list)
{
    typedef void (*end_func)(NCParamList *);
    static end_func real_end;

    if (!real_end) {
        real_end = (end_func)dlsym(RTLD_NEXT, "nc_param_list_end");
        if (!real_end) {
            fprintf(stderr, "cannot resolve nc_param_list_end\n");
            abort();
        }
    }
    if (!observed_param_list && output_directory()) {
        observed_param_list = param_list;
        save_snapshot("initial", 0);
    }
    real_end(param_list);
}

void nc_sgd_opt_update(NCSGDOptState *state)
{
    typedef void (*update_func)(NCSGDOptState *);
    static update_func real_update;

    if (!real_update) {
        real_update = (update_func)dlsym(RTLD_NEXT, "nc_sgd_opt_update");
        if (!real_update) {
            fprintf(stderr, "cannot resolve nc_sgd_opt_update\n");
            abort();
        }
    }
    real_update(state);
    observed_update_count++;
    save_snapshot("update", observed_update_count);
}
