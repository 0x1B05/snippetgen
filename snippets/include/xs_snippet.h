#ifndef XS_SNIPPET_H
#define XS_SNIPPET_H

#include "xsrt_env.h"

typedef struct {
  const char *id;
  int (*init)(xsrt_env_t *env);
  int (*run)(xsrt_env_t *env);
  int (*check)(xsrt_env_t *env);
  void (*fini)(xsrt_env_t *env);
} xsrt_snippet_desc_t;

int xsrt_run_snippet(xsrt_env_t *env, const xsrt_snippet_desc_t *snippet);
int xsrt_run_snippet_no_check(xsrt_env_t *env, const xsrt_snippet_desc_t *snippet);
int xsrt_run_snippet_check_only(xsrt_env_t *env, const xsrt_snippet_desc_t *snippet);

#endif
