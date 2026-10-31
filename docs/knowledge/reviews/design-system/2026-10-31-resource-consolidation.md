# Shared resource consolidation — 2026-10-31

Baseline: `348d1a0`. Every window loads `KLCodeComponents.xaml`, which loaded
the rest of an eight-file chain, so most of the splits were organisational
only. The owner approved folding them into four files; the
[design system guide](../../../DESIGNSYSTEM.md) owns the resulting
architecture table.

| File | Holds |
| --- | --- |
| `KLCodeTokens.xaml` | Palette, foundation tokens, Command Switch pill tokens, new scrollbar tokens and the chrome data (footer URIs, default labels) |
| `klIcons.xaml` | Generated icon geometry and the `klcLogo` template (unchanged) |
| `KLCodeFoundation.xaml` | Merges the two above; adds the scrollbar and footer-link styles from the former shared primitives |
| `KLCodeComponents.xaml` | Merges Foundation; adds the Command Switch pill styles |

Removed: `KLCode_palette.xaml`, `KLCodeFoundationTokens.xaml`,
`KLCodeChrome.xaml`, `KLCodeSharedPrimitives.xaml` and
`KLCodeCommandSwitch.xaml`. The tokens file was built mechanically from them,
so no value changed. Within it, values come before anything that refers to
them, because WPF resolves StaticResource only against keys already defined.
The scrollbar's literal 3 / 10 / 2 / 8 became `KlaScrollBarMargin`,
`KlaScrollBarRadius`, `KlaScrollThumbMargin` and `KlaScrollThumbRadius`, since
Foundation is under the strict token lint; the lint no longer exempts any
shared dictionary. The Command Switch now loads Components like every other
window.

Verification (macOS): every resource key from the eight files is still
defined (217 before, 221 after: the four scrollbar tokens), none is defined
twice in one file, every StaticResource and DynamicResource reference in the
repository resolves, and every XAML file parses. 435 Python tests with the one
existing macOS path-case failure; C# source contracts 17 of 17 (they now check
the three hand-written dictionaries are event-free and the compiled project
links them); the Windows smoke project builds; scale lint 0 strict / 62
advisory; metadata audit clean. Not rendered on Windows; the compiled add-ins
pick the change up at their next rebuild.
