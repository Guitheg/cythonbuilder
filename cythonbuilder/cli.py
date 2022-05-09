import logging
import os
import sys

from cythonbuilder import cythonbuilder
from cythonbuilder import appsettings
from cythonbuilder import helpers
from cythonbuilder.services import logger

def display_help():
    print(f"""{appsettings.package_name}
        Automatically builds and packages your Cython code 
        1. Initialize {appsettings.package_name} with `{appsettings.console_name} init` 
        3. Call `{appsettings.console_name} build` to build and package all .pyx files in your project 

        Commands:
        (call either command with -v to display more information)
        help        Show this screen
        init        Create 'ext' and 'ext/annotations' folders
        list        Lists all pyx files in your project that can be built
                    Pass a space-separated list of filenames (with or without .pyx) to filter
        build       Finds and builds all pyx files in your project (excluding venv directories) package cython files. Then cleans the project (see cybuilder clean)
                    Pass a space-separated list of filenames (with or without .pyx) to filter.
                    Options:
                      --include-numpy   Includes numpy (default False)
                      --no-annotation   Disables generating the annotations html (default True)
                      --no-cleanup      Prevents removal of intermediate C files generated by Cython (default True)
        clean       Moves all generated .html files to ext/annotations 
                    Pass a space-separated list of filenames (with or without .pyx) to filter.
                    Options:
                      --no-cleanup      Prevents removal of intermediate C files generated by Cython (default True)
    """)
    quit()

def main():
    """ Parse command line """

    args = sys.argv[1:]

    # Preferences
    # FORCE = '-f' in args or '--force' in args
    VERBOSE = '-v' in args or '--verbose' in args
    ACCEPT = '-y' in args or '--yes' in args
    # OVERWRITE = '-o' in args or '--overwrite' in args
    for flag in ['-f', '--force', '-v', '--verbose', '-y', '--accept', '-o', '--overwrite']:
        args.remove(flag) if (flag in args) else None


    # Logging level
    if (VERBOSE):
        from cythonbuilder.logs import set_format
        set_format(logger=logger, format=f"[%(name)s] %(asctime)s %(module)-8s %(lineno)-3d  %(message)s")
        logger.setLevel(logging.DEBUG)



    # Parse arguments - Must provide at least one argument
    if (len(args) == 0):
        display_help()
    cmd1 = helpers.CliTools.pop_arg_or_exit(arglist=args, errormessage=f"[{appsettings.package_name}] {appsettings.package_name} expects at least one argument. Check out [helpy help] for more information")
    logger.debug(msg=f"{cmd1=}")


    # HELPY functions
    if (cmd1 == 'init'):
        logger.info(msg=f"[{cmd1}] - Initializing..")
        cythonbuilder.init_cython()
        logger.info(msg=f"[{cmd1}] - Initialized")
        quit()
    elif (cmd1 == 'list'):
        # Lists all pyx files that can be built
        target_filenames = args if (len(args) > 0) else None
        filtermsg = f" (filtered by {target_filenames}) " if (target_filenames) else ""

        logger.info(msg=f"Listing all pyx files{filtermsg}:")
        target_pyx_files_fullpaths: [str] = cythonbuilder.cython_find_pyx_files(target_files=target_filenames)
        for foundfile in target_pyx_files_fullpaths:
            logger.info(msg=f"\t{foundfile}")
        logger.info(msg=f"Listed all pyx files")
    elif (cmd1 == 'build'):
        # Get arguments
        include_numpy = '--include-numpy' in args
        dont_generate_annotations = '--no-annotations' in args
        dont_cleanup = '--no-cleanup' in args
        args = [a for a in args if (a not in ['--no-annotations', '--include-numpy', '--no-cleanup'])]
        target_filenames = args if (len(args) > 0) else None

        # Validate arguments
        numpy_is_installed = helpers.package_is_installed(package_import_name='numpy')
        if (include_numpy and not numpy_is_installed):
            if (
                    input(f"[{appsettings.package_name} {cmd1}] You want to include numpy but your current project does not have numpy installed. Install numpy? (y/n)").lower() == 'y'):
                logger.warning(msg=f"Please install numpy with [pip install numpy]")
                quit()
            else:
                include_numpy = False
        if (not include_numpy and numpy_is_installed):
            if (input(f"[{appsettings.package_name} {cmd1}] Your current project uses numpy. Do you want to include numpy in your Cython build? (y/n)").lower() == 'y'):
                include_numpy = True

        logger.info(msg=f"[{cmd1}] - Building Cython files..")
        try:
            target_pyx_files_fullpaths: [str] = cythonbuilder.cython_find_pyx_files(target_files=target_filenames)
            logger.debug(msg=f"Found {len(target_pyx_files_fullpaths)} to build")
            if (not ACCEPT):
                __formatted_package_list = "\n".join(f"\t - {file}" for file in target_pyx_files_fullpaths)
                if (input(f"[{appsettings.package_name} {cmd1}] these {len(target_pyx_files_fullpaths)} pyx files?\n(y/n) \n {__formatted_package_list}").lower() != "y"):
                    logger.info(msg="Exiting..", )
                    quit()
            logger.debug(msg=f"Building {len(target_pyx_files_fullpaths)} pyx files")
            cythonbuilder.cython_build(
                target_files=target_pyx_files_fullpaths,
                create_annotations=not dont_generate_annotations,
                include_numpy=include_numpy,
            )
            logger.debug(msg=f"Built {len(target_pyx_files_fullpaths)} pyx files, cleaning up..")
            cythonbuilder.cython_clean(target_files=target_pyx_files_fullpaths, keep_c_files=dont_cleanup)
            logger.debug(msg=f"Cleanup complete")
            logger.info(msg=f"[{cmd1}] - Cython build success")
        except Exception as e:
            logger.error(msg=f"[{cmd1}] build error: {e}")
            quit()
    elif (cmd1 == 'clean'):
        # Get arguments
        dont_cleanup = '--no-cleanup' in args
        args = [a for a in args if (a not in ['--no-cleanup'])]
        target_filenames = args if (len(args) > 0) else None

        # Clean
        logger.info(msg=f"[{cmd1}] - Building Cython files..")
        try:
            target_pyx_files_fullpaths: [str] = cythonbuilder.cython_find_pyx_files(target_files=target_filenames)
            logger.debug(msg=f"Found {len(target_pyx_files_fullpaths)} to build")
            if (not ACCEPT):
                __formatted_package_list = "\n".join(f"\t - {file}" for file in target_pyx_files_fullpaths)
                if (input(f"[{appsettings.package_name} {cmd1}] these {len(target_pyx_files_fullpaths)} pyx files?\n(y/n) \n {__formatted_package_list}").lower() != "y"):
                    logger.info(msg="Exiting..", )
                    quit()
            logger.debug(msg=f"Cleaning {len(target_pyx_files_fullpaths)} pyx files")
            cythonbuilder.cython_clean(target_files=target_pyx_files_fullpaths, keep_c_files=dont_cleanup)
            logger.debug(msg=f"Cleanup complete")
            logger.info(msg=f"[{cmd1}] - Cython build success")
        except Exception as e:
            logger.error(msg=f"[{cmd1}] build error: {e}")
            quit()
    elif (cmd1 == 'help'):
        display_help()
    else:
        logger.warning(msg=f"unknown command: '{cmd1}'")
        display_help()


if __name__ == "__main__":
    # main()
    help(cythonbuilder)