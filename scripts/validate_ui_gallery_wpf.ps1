param(
    [string]$EngineDirectory = "$env:APPDATA/pyRevit-Master/bin/netfx/engines/IPY2712PR",
    [string]$OutputDirectory = ''
)
# Isolated .NET Framework WPF validation, without a Revit process or model.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationFramework,PresentationCore,WindowsBase,System.IO.Compression
$galleryEngineAssembly = [Reflection.Assembly]::LoadFrom((Join-Path $EngineDirectory 'pyRevitLabs.IronPython.dll'))
$galleryModulesAssembly = [Reflection.Assembly]::LoadFrom((Join-Path $EngineDirectory 'pyRevitLabs.IronPython.Modules.dll'))
$galleryWpfAssembly = [Reflection.Assembly]::LoadFrom((Join-Path $EngineDirectory 'pyRevitLabs.IronPython.Wpf.dll'))
$galleryRunnerAssembly = [Reflection.Assembly]::LoadFrom((Join-Path $EngineDirectory 'pyRevitRunner.dll'))
$galleryEngine = [IronPython.Hosting.Python]::CreateEngine()
foreach ($galleryAssembly in @($galleryEngineAssembly, $galleryModulesAssembly, $galleryWpfAssembly,
                              [Windows.Window].Assembly, [IO.Compression.ZipArchive].Assembly)) {
    $galleryEngine.Runtime.LoadAssembly($galleryAssembly)
}
$galleryScope = $galleryEngine.CreateScope()
$galleryScope.SetVariable('stdlib_stream', $galleryRunnerAssembly.GetManifestResourceStream('pyRevitRunner.python_2712pr_lib.zip'))
$galleryScope.SetVariable('repo_root', (Split-Path -Parent $PSScriptRoot))
$galleryScope.SetVariable('output_directory', $OutputDirectory)
$galleryBootstrap = @'
import sys
import clr
from System.IO import StreamReader
from System.IO.Compression import ZipArchive, ZipArchiveMode

# Consume the installed runner's library in memory; no upstream files are copied.
class EmbeddedLibrary(object):
    def __init__(self, stream):
        self.archive = ZipArchive(stream, ZipArchiveMode.Read)
        self.entries = dict((entry.FullName, entry) for entry in self.archive.Entries)

    def find_module(self, fullname, path=None):
        name = fullname.replace('.', '/')
        return self if name + '.py' in self.entries or name + '/__init__.py' in self.entries else None

    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]
        name = fullname.replace('.', '/')
        package = name + '/__init__.py' in self.entries
        source_name = name + '/__init__.py' if package else name + '.py'
        module = type(sys)(fullname)
        module.__file__ = repo_root + '/installed_stdlib/' + source_name
        module.__loader__ = self
        if package:
            module.__path__ = [repo_root + '/installed_stdlib/' + name]
        sys.modules[fullname] = module
        reader = StreamReader(self.entries[source_name].Open())
        try:
            source = reader.ReadToEnd()
        finally:
            reader.Dispose()
        exec compile(source.encode('utf-8'), module.__file__, 'exec') in module.__dict__
        return module

sys.meta_path.append(EmbeddedLibrary(stdlib_stream))
sys.dont_write_bytecode = True
sys.path.insert(0, repo_root + '/lib')
execfile(repo_root + '/scripts/validate_ui_gallery_wpf.py')
'@
try {
    $galleryEngine.Execute($galleryBootstrap, $galleryScope) | Out-Null
} catch {
    $galleryFailure = $_.Exception
    $galleryGetService = $galleryEngine.GetType().GetMethods() | Where-Object { $_.Name -eq 'GetService' -and $_.IsGenericMethod } | Select-Object -First 1
    $galleryServiceArguments = New-Object object[] 1
    $galleryServiceArguments[0] = [object[]]@()
    $galleryFormatter = $galleryGetService.MakeGenericMethod([Microsoft.Scripting.Hosting.ExceptionOperations]).Invoke($galleryEngine, $galleryServiceArguments)
    Write-Output ($galleryFormatter.FormatException($galleryFailure.InnerException))
    throw
} finally {
    $galleryEngine.Runtime.Shutdown()
}
