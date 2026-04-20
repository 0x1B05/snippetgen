#include "xs_snippet.h"

static int xsrt_run_snippet_internal(
    xsrt_env_t *env,
    const xsrt_snippet_desc_t *snippet,
    int do_init,
    int do_run,
    int do_check,
    int do_fini) {
  int rc;

  if (env == 0 || snippet == 0) {
    return -1;
  }

  if (do_init && snippet->init != 0) {
    rc = snippet->init(env);
    if (rc != 0) {
      if (do_fini && snippet->fini != 0) {
        snippet->fini(env);
      }
      return rc;
    }
  }

  if (do_run && snippet->run != 0) {
    rc = snippet->run(env);
    if (rc != 0) {
      if (do_fini && snippet->fini != 0) {
        snippet->fini(env);
      }
      return rc;
    }
  }

  if (do_check && snippet->check != 0) {
    rc = snippet->check(env);
    if (rc != 0) {
      if (do_fini && snippet->fini != 0) {
        snippet->fini(env);
      }
      return rc;
    }
  }

  if (do_fini && snippet->fini != 0) {
    snippet->fini(env);
  }

  return 0;
}

int xsrt_run_snippet(xsrt_env_t *env, const xsrt_snippet_desc_t *snippet) {
  return xsrt_run_snippet_internal(env, snippet, 1, 1, 1, 1);
}

int xsrt_run_snippet_no_check(xsrt_env_t *env, const xsrt_snippet_desc_t *snippet) {
  return xsrt_run_snippet_internal(env, snippet, 1, 1, 0, 1);
}

int xsrt_run_snippet_check_only(xsrt_env_t *env, const xsrt_snippet_desc_t *snippet) {
  return xsrt_run_snippet_internal(env, snippet, 0, 0, 1, 0);
}
