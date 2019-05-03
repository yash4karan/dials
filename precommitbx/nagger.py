from __future__ import absolute_import, division, print_function

import os
import sys


def nag():
    """
    Check if pre-commits should be installed for this repository.
    If they are not and should be then annoy the developer.
    To be called in libtbx_refresh.py
    """
    if os.name == "nt":  # unsupported
        return
    # Determine the name of the calling module, and thus the internal module name
    # of the libtbx_refresh file. Use exception trick to pick up the current frame.
    try:
        raise Exception()
    except Exception:
        frame = sys.exc_info()[2].tb_frame.f_back
    # Extract the caller name
    caller = frame.f_globals["__name__"]
    if caller == "__main__":
        # well that is not very informative, is it.
        caller = os.path.abspath(
            frame.f_code.co_filename
        )  # Get the full path of the libtbx_refresh.py file.
        refresh_file, _ = os.path.splitext(caller)
        if not refresh_file.endswith("libtbx_refresh"):
            raise RuntimeError(
                "pre-commit nagging can only be done from within libtbx_refresh.py"
            )
        # the name of the parent directory of libtbx_refresh.py is the caller name
        caller = os.path.basename(os.path.dirname(refresh_file))
    else:
        if not caller.endswith(".libtbx_refresh"):
            raise RuntimeError(
                "pre-commit nagging can only be done from within libtbx_refresh.py"
            )
        caller = caller[:-15]

    try:
        import libtbx.load_env
    except Exception as e:
        print("error on importing libtbx environment for pre-commit nagging:", e)
        return
    try:
        path = libtbx.env.dist_path(caller)
    except Exception as e:
        print(
            "error on obtaining module path for %s for pre-commit nagging:" % caller, e
        )
        return

    if not os.path.isdir(os.path.join(path, ".git")):
        return  # not a developer installation

    precommit_python = abs(libtbx.env.build_path / "precommitbx" / "bin" / "python3")
    hookfile = os.path.join(path, ".git", "hooks", "pre-commit")
    if os.path.isfile(hookfile) and os.access(hookfile, os.X_OK):
        with open(hookfile, "r") as fh:
            precommit = fh.read()
        if "precommitbx" in precommit and os.path.exists(precommit_python):
            return  # libtbx.precommit hook is fine
        if "generated by pre-commit" in precommit and "libtbx" not in precommit:
            return  # genuine pre-commit hook is also fine

    import dials.precommitbx.installer

    def fprint(text=""):
        print("= {0:<56s} =".format(text))

    print(dials.precommitbx.installer.YELLOW + "=" * 60)
    fprint()
    fprint("You appear to be running on a development installation,")
    fprint("however the source directory for %s" % caller)
    fprint("does not have the mandatory pre-commits installed.")
    fprint()
    fprint("Please run")
    fprint("  libtbx.precommit install")
    fprint("before making any commits to this repository.")
    fprint()
    print("=" * 60 + dials.precommitbx.installer.NC)

    # import time
    # time.sleep(0.3)
