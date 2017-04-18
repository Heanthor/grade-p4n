import argparse
import os
import pprint
import platform
import subprocess
import webbrowser
import re

def output(line, error=False):
    indent = "*** " if error else "    "

    print "%s%s" % (indent, line)

# returns a list of files in subdirectories of dir, with optional suffix filter
def list_files(directory, suffix=None):
    r = []
    subdirs = [x[0] for x in os.walk(directory)]

    for subdir in subdirs:
        files = os.walk(subdir).next()[2]

        if len(files) > 0:
            for f in files:
                if suffix is not None:
                    if suffix in f:
                        r.append(subdir + "/" + f)
                else:
                    r.append(subdir + "/" + f)
    return [x.replace("\\", "/") for x in r]

def check_oo(file_list):
    # checking only php files for OO sql access, or a class

    pattern = re.compile('(class\s[a-zA-Z]*\s*\n*{)')
    for fl in file_list:
        with open(fl, 'r') as f:
            text = f.read()

            if 'new mysqli' in text:
                return "new mysqli"

            m = pattern.search(text)
            if m:
                # didn't use OO sql, made their own class
                return m.groups()[0]

    return False

def check_selfref(file_list):
    s = "$_SERVER['PHP_SELF']"
    s2 = "$_SERVER[\"PHP_SELF\"]"

    for fl in file_list:
        fname = os.path.basename(fl)

        with open(fl, 'r') as f:
            text = f.read()

            if s in text or s2 in text:
                return s

            if fname in text:
                # still self referencing if the file name is hardcoded
                return fname

    return False

def check_hidden(file_list):
    for fl in file_list:
        fname = os.path.basename(fl)

        with open(fl, 'r') as f:
            text = f.read()

            if "hidden" in text:
                # possibility of a false positive, but this should be pretty rare
                # return file name for manual checking
                return fname

    return True

def check_admin_login(file_list):
    l = "$_SERVER['PHP_AUTH_USER']"

    for fl in file_list:
        with open(fl, 'r') as f:
            text = f.read()

            if l in text:
                return True

    return False

def check_crypt_basic(file_list):
    # hopefully one of these two will be used,
    # or they don't have spaces after their functions
    crypt_funcs = ["password_hash", "crypt"]

    for fl in file_list:
        with open(fl, 'r') as f:
            text = f.read()

            for crypt_func in crypt_funcs:
                if crypt_func in text:
                    return crypt_func

    return False

def main(start_dir):
    print "--- CMSC389N ApplicationSystem Grading Script ---\n"

    # file every project must have, to identify unique folders
    unique_file = "main.html"

    html_projects = list_files(start_dir, unique_file)
    # people not doing the project right
    php_mains = list_files(start_dir, "main.php")

    projects = html_projects + php_mains

    i = len(next(os.walk(start_dir))[1])

    if len(projects) != i:
        print("Not all projects accessible (%d expected, %d found)" % (i, len(projects)))

        zp1 = list_files(start_dir, ".rar")
        zipped_projects = list_files(start_dir, ".zip") + zp1

        if zipped_projects:
            print "Some projects are compressed, make sure to check manually:"
            pprint.pprint(zipped_projects)

            print "\n"

    print "--- Grading Loop ---"
    print "Press enter to move to next file"

    # wait
    raw_input("\n")

    for f in projects:
        print "File: " + f
        print "Username: " + filter(lambda x: "__" in x, f.split("/"))[0]
        xampp_path = f[f.find("htdocs") + len("htdocs"):]
        folder_path = f[:f.rfind("/")]

        # build windows path
        if platform.system() == "Windows":
            print "Folder Path %s" % folder_path
            folder_path = folder_path.replace("/", "\\")
            subprocess.call("start %s" % folder_path, shell=True)
        else:
            subprocess.call("open '%s'" % folder_path, shell=True)

        webbrowser.open("http://localhost" + xampp_path)

        php_files = list_files(folder_path, ".php")

        # check requirements
        if ".php" in f:
            output("main page is a php file, not html!", True)

        result = check_oo(php_files)

        if not result:
            output("No OO found (-15)!", True)
        else:
            output("Found OO (%s)!" % result)

        result = check_selfref(php_files)

        if not result:
            output("No self referencing found (-5)!", True)
        else:
            output("Found self referencing (%s)!" % result)

        result = check_hidden(php_files)

        if not result:
            output("Found string 'hidden' in %s (-5)!" % result, True)
        else:
            output("No hidden form fields!")

        if not check_admin_login(php_files):
            output("No admin login code found (-5)!", True)
        else:
            output("Found admin login code!")

        result = check_crypt_basic(php_files)

        if not result:
            output("No crypt function found (-5)!", True)
        else:
            output("Found crypt function!")
        # wait
        raw_input("\n")

if __name__ == "__main__":
    if sys.version_info >= (3, 0):
    sys.stdout.write("Sorry, requires Python 2.x, not Python 3.x\n")
    sys.exit(1)
    
    parser = argparse.ArgumentParser()
    parser.add_argument('start_dir', type=str,
    help="Path to the folder containing project folders")

    args = parser.parse_args()

    main(vars(args)["start_dir"])
