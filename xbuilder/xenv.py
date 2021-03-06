import os
import platform
import SCons
import xunit_test

thisDir = os.path.dirname(__file__)
parentDir = os.path.abspath(os.path.join(thisDir, os.path.pardir))

def _is_windows():
    return platform.system() == 'Windows'

def _is_linux():
    return platform.system() == 'Linux'

def current_architecture():
    return 'x86_64'

def detect_boost_path():
    if os.environ.has_key('BOOST_DIR'):
        return os.environ['BOOST_DIR']
    return os.path.join(parentDir, 'vendor', 'boost_1_49_0')

def detect_boost_lib_path():
    if os.environ.has_key('BOOST_LIB_DIR'):
        return os.environ['BOOST_LIB_DIR']
    boost_dir = detect_boost_path()
    boost_lib_dir = os.path.join(boost_dir, 'stage', 'lib')
    if os.path.exists(boost_lib_dir):
        return boost_lib_dir
    elif '64' in current_architecture():
        boost_lib_dir = os.path.join(boost_dir, 'stage', 'lib64')
    if os.path.exists(boost_lib_dir):
        return boost_lib_dir
    else:
        boost_lib_dir = os.path.join(boost_dir, 'stage', 'lib32')
    if os.path.exists(boost_lib_dir):
        return boost_lib_dir
    return boost_dir

def detect_gmock_path():
    if os.environ.has_key('GOOGLE_DIR'):
        return os.environ['GOOGLE_DIR']
    return os.path.join(parentDir, 'vendor', 'google')

def display(message):
    print 'scons: ' + message

vars = SCons.Variables.Variables(None, SCons.Script.ARGUMENTS)
vars.Add(SCons.Variables.BoolVariable('unicode', 'Use unicode string', True))
vars.Add(SCons.Variables.BoolVariable('release', 'Build without debug information', False))
vars.Add(SCons.Variables.PathVariable('boost', 'Include directory for boost', detect_boost_path()))
vars.Add(SCons.Variables.PathVariable('boost_lib', 'Library directory for boost', detect_boost_lib_path()))
vars.Add(SCons.Variables.PathVariable('google', 'Include directory for google mock framework', detect_gmock_path()))

if _is_windows():
    #
    windows_name_to_nt_value = { 'win2k' : 0x0500, 'winxp' : 0x0501,
                                 'win2k3' : 0x0502, 'winvista' : 0x0600, 'win7' : 0x0601 }
    #
    def current_windows_name():
        version = platform.version()
        major, minor, build = version.split('.')
        if major == '5':
            if minor == '0':
                return 'win2k'
            elif minor == '1':
                return 'winxp'
            elif minor == '2':
                return 'win2k3'
        elif major == '6':
            if minor == '0':
                return 'winvista'
            elif minor == '1':
                return 'win7'
        # Return lowest supported by Windows SDK
        return 'win2k'
    #
    vars.Add(SCons.Variables.EnumVariable('windows', 'Specify target platform', current_windows_name(), windows_name_to_nt_value.keys()))
    from SCons.Tool.MSCommon.vc import get_installed_vcs
    supported_msvc_list = get_installed_vcs()
    # Use the first one as the default version
    vars.Add(SCons.Variables.EnumVariable('msvc', 'Specify Visual Studio version', supported_msvc_list[0], supported_msvc_list))

architectures = [ 'x86', 'i386', 'amd64', 'emt64', 'x86_64', 'ia64' ]

vars.Add(SCons.Variables.EnumVariable('arch', 'Specify target architecture', current_architecture(), architectures))

kwargs = {}

if SCons.Script.ARGUMENTS.has_key('arch'):
    kwargs['TARGET_ARCH'] = SCons.Script.ARGUMENTS['arch']

# Currently, we prefer Visual Studio 2008
if _is_windows() and SCons.Script.ARGUMENTS.has_key('msvc'):
    msvc_version = SCons.Script.ARGUMENTS['msvc']
    if msvc_version in supported_msvc_list:
        kwargs['MSVC_VERSION'] = msvc_version

xenv = SCons.Defaults.DefaultEnvironment(ENV = os.environ, variables = vars, **kwargs)
xenv.Help(vars.GenerateHelpText(xenv))

def use_boost(xenv, *libs):
    boost_dir = xenv['BOOST_DIR']
    boost_lib_dir = xenv['BOOST_LIB_DIR']
    xenv.Append(CPPPATH = [boost_dir], LIBPATH = [boost_lib_dir])
    if is_linux(xenv):
        libs = ('boost_locale', 'boost_system', 'boost_thread', 'boost_program_options')
    if libs:
        xenv.Append(LIBS = [lib for lib in libs])
    # These flags must be after those boost libs, this is restricted by Linux
    if is_linux(xenv):
        # Check if ICU works, if yes, then get the flags
        icu_config = xenv.WhereIs('icu-config')
        if icu_config:
            # Run '/usr/bin/icu-config --ldflags' to retrieve flags
            retrieve_icu_ldflags = '%s --ldflags' % icu_config
            xenv.ParseConfig(retrieve_icu_ldflags)

def use_gmock(xenv):
    google_dir = xenv['GOOGLE_DIR']
    xenv.Append(CPPPATH = [google_dir])

def gmock_sources(xenv):
    google_dir = xenv['GOOGLE_DIR']
    sources = ['gmock_main.cc', 'gmock-gtest-all.cc']
    return [os.path.join(google_dir, source) for source in sources]

def gmock_objects(xenv):
    sources = gmock_sources(xenv)
    objects = [os.path.basename(source) for source in sources]
    objects = [obj.replace('.cc', xenv['OBJSUFFIX']) for obj in objects]
    built_objects = []
    for index in range(len(sources)):
        built_objects += xenv.Object(objects[index], sources[index])
    return built_objects

def is_windows(xenv):
    return platform.system() == 'Windows'

def is_linux(xenv):
    return platform.system() == 'Linux'

def is_mac(xenv):
    return platform.system() == 'darwin'

def is_debug(xenv):
    return not xenv['release']

def is_unicode(xenv):
    return xenv['unicode']

def windows_version_value(xenv):
    return windows_name_to_nt_value[xenv['windows']]

def with_preprocessed_file(xenv):
    return False

def is_target_arch_64(xenv):
    arch = xenv['TARGET_ARCH']
    if not arch:
        arch = os.uname()[-1]
    return arch.find('64') >= 0

def setup(xenv, component = 'build'):
    configuration = 'debug' if is_debug(xenv) else 'release'
    configuration += '_unicode' if is_unicode(xenv) else '_ansi'
    system = platform.system().lower()
    arch = xenv['TARGET_ARCH']
    # arch might be None
    if arch:
        build_output = os.path.join('%s_output' % component, system, arch, configuration)
    else:
        build_output = os.path.join('%s_output' % component, system, configuration)
    # Setup paths
    xenv['BOOST_DIR'] = xenv['boost']
    # IF the path is passed with command line option or set by environment variable
    # We will take it
    if SCons.Script.ARGUMENTS.has_key('boost_lib') or os.environ.has_key('boost_lib'):
        xenv['BOOST_LIB_DIR'] = xenv['boost_lib']
    # Otherwise, we need to check it carefully
    else:
        if xenv.IsTargetArch64():
            xenv['BOOST_LIB_DIR'] = os.path.join(xenv['BOOST_DIR'], 'stage', 'lib64')
        else:
            xenv['BOOST_LIB_DIR'] = os.path.join(xenv['BOOST_DIR'], 'stage', 'lib32')
        if not os.path.exists(xenv['BOOST_LIB_DIR']):
            xenv['BOOST_LIB_DIR'] = os.path.join(xenv['BOOST_DIR'], 'stage', 'lib')
    xenv['GOOGLE_DIR'] = xenv['google']

    if is_unicode(xenv):
        xenv.Append(CPPDEFINES = ['UNICODE', '_UNICODE'])
    if not is_debug(xenv):
        xenv.Append(CPPDEFINES = ['NDEBUG'])
    else:
        xenv.Append(CPPDEFINES = ['DEBUG', '_DEBUG'])
        if not is_windows(xenv):
            xenv.Append(CCFLAGS = ['-g'])
    #
    if is_windows(xenv):
        display("Building the application by MSVC %s" % xenv["MSVC_VERSION"])
        xenv.Replace(WINDOWS_EMBED_MANIFEST = True, WINDOWS_INSERT_DEF = True)
        # /W3 - warning level
        # /wd4819 - disable warning with number 4819, which is about a file containing unicode chars, but the file was not saved as unicode
        xenv.Append(CCFLAGS = ['/EHsc', '/Gd', '/W3', '/wd4819'])
        # /Zc:wchar_t- - do not treat wchar_t as builtin type, if this option applied, wchar_t will be treated as unsigned int
        # xenv.Append(CCFLAGS = ['/Zc:wchar_t-'])
        # /P - generate preprocessor file with line number
        # /EP /P - generate preprocessor file without line number
        if with_preprocessed_file(xenv):
            xenv.Append(CCFLAGS = ['/P'])
        # Use this option to define wchar_t as unsigned short
        # It will introduce a problem when formatting a unsigned short integer to a string
        # It will fail because the library is not able to tell if given a unsigned short is a character or a number
        #xenv.Append(CCFLAGS = ['/Zc:wchar_t-'])
        xenv.Append(CPPDEFINES = ['WINDOWS', '__WINDOWS__', '_CRT_SECURE_NO_WARNINGS', '_SCL_SECURE_NO_WARNINGS', '_WIN32_WINNT=0x%04x' % windows_version_value(xenv)])
        # Values for _WIN32_WINNT
        # 0x0500 for Windows 2000
        # 0x0501 for Windows XP
        # 0x0502 for Windows Server 2003
        # 0x0600 for Windows Vista
        # 0x0601 for Windows 7
        if is_debug(xenv):
            xenv.Append(CCFLAGS = ['/Od', '/MDd', '/RTC1'], LINKFLAGS = ['/DEBUG'], ARFLAGS = [])
        else:
            xenv.Append(CCFLAGS = ['/O2', '/Oi', '/Ot', '/Gy', '/MD', '/GL'], LINKFLAGS = ['/LTCG', '/OPT:REF', '/OPT:ICF'], ARFLAGS = ['/LTCG'])
    elif is_linux(xenv):
        xenv.Append(CPPDEFINES = ['LINUX', '__LINUX__'], LIBS = ['pthread'])
    elif is_mac(xenv):
        xenv.Append(CPPDEFINES = ['MACOSX', '__MACOSX__'])
    #
    elif is_linux(xenv):
        xenv.Append(CPPDEFINES = ['LINUX', '__LINUX__'])
    elif is_mac(xenv):
        xenv.Append(CPPDEFINES = ['MACOSX', '__MACOSX__'])
    xenv.VariantDir(build_output, '.', duplicate = False)
    return build_output

def pdb_name_of(target_name):
    program = os.path.basename(target_name)
    program = os.path.splitext(program)[0]
    return program + '.pdb'

def build_program(xenv, *args, **kwargs):
    if is_windows(xenv):
        xenv['PDB'] = pdb_name_of(args[0])
    return xenv.Program(*args, **kwargs)

def build_static_library(xenv, *args, **kwargs):
    if is_windows(xenv):
        xenv['PDB'] = pdb_name_of(args[0])
    return xenv.StaticLibrary(*args, **kwargs)

def build_shared_library(xenv, *args, **kwargs):
    if is_windows(xenv):
        xenv['PDB'] = pdb_name_of(args[0])
    return xenv.SharedLibrary(*args, **kwargs)

def build_unit_test(xenv, *args, **kwargs):
    program = xenv.Program(*args, **kwargs)
    test_result = xenv.RunUnitTest(program)
    xenv.Clean(program, test_result)
    return program

def testee_objects(xenv, sources):
    objects = [os.path.basename(str(source)) for source in sources]
    objects = [os.path.splitext(obj)[0] for obj in objects]
    objects = [obj + xenv['OBJSUFFIX'] for obj in objects]
    built_objects = []
    for index in range(len(sources)):
        built_objects += xenv.Object(objects[index], sources[index])
    return built_objects

def is_debugging_unit_test(xenv):
    return False

def setup_test_env(xenv):
    xenv.Append(CPPDEFINES = [])

# Add methods
xenv.AddMethod(use_boost, 'UseBoost')
xenv.AddMethod(use_gmock, 'UseGoogleMock')
xenv.AddMethod(is_windows, 'IsWindows')
xenv.AddMethod(is_linux, 'IsLinux')
xenv.AddMethod(is_mac, 'IsMac')
xenv.AddMethod(is_debug, 'IsDebug')
xenv.AddMethod(is_unicode, 'IsUnicode')
xenv.AddMethod(gmock_sources, 'GoogleMockSources')
xenv.AddMethod(gmock_objects, 'GoogleMockObjects')
xenv.AddMethod(with_preprocessed_file, 'WithPreprocessedFile')
xenv.AddMethod(setup, 'Setup')
xenv.AddMethod(build_program, 'BuildProgram')
xenv.AddMethod(build_static_library, 'BuildStaticLibrary')
xenv.AddMethod(build_shared_library, 'BuildSharedLibrary')
xenv.AddMethod(build_unit_test, 'BuildUnitTest')
xenv.AddMethod(testee_objects, 'TesteeObjects')
xenv.AddMethod(testee_objects, 'LocalObjects')
xenv.AddMethod(setup_test_env, 'SetupTestEnv')
xenv.AddMethod(is_debugging_unit_test, 'IsDebuggingUnitTest')
xenv.AddMethod(is_target_arch_64, 'IsTargetArch64')
# Add builders
xenv.Append(BUILDERS = {'RunUnitTest' : xunit_test.RunUnitTest})
