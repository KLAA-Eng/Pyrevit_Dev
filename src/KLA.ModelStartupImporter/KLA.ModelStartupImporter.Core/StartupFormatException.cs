using System;

namespace KLA.ModelStartupImporter.Core;

internal sealed class StartupFormatException : Exception
{
    internal StartupFormatException(string message)
        : base(message)
    {
    }
}
