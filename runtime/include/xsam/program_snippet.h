#ifndef XSAM_PROGRAM_SNIPPET_H
#define XSAM_PROGRAM_SNIPPET_H

#include "xsrt_env.h"
#include "xs_snippet.h"

typedef int (*xsam_program_main_t)(void);

xsrt_env_t *xsam_current_env(void);
int xsam_run_program_main(xsrt_env_t *env, xsam_program_main_t entry);

#define XSAM_DEFINE_PROGRAM_SNIPPET(symbol, snippet_id, entry_fn)               \
  static int symbol##_run(xsrt_env_t *env) {                                    \
    return xsam_run_program_main(env, (entry_fn));                              \
  }                                                                             \
  const xsrt_snippet_desc_t symbol = {                                          \
      .id = (snippet_id),                                                       \
      .init = 0,                                                                \
      .run = symbol##_run,                                                      \
      .check = 0,                                                               \
      .fini = 0,                                                                \
  }

#endif
