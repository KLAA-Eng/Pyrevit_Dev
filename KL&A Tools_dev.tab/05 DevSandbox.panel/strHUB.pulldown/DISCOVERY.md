# strHUB discovery and compatibility evidence

Recorded: 2026-10-29. Status: both interview rounds answered;
the draft [SPEC.md](SPEC.md) awaits approval.

This file owns discovery evidence and the interview history. [SPEC.md](SPEC.md)
owns the proposed requirements. Neither is evidence of a working exporter.
All strHUB outputs remain under this pulldown at the user's request, overriding
the repository's usual central documentation locations for this effort.

## Intent and current scope

The user's long-term goal is a suite for transferring structural models among
multiple analysis applications, eventually with round trips. The initial direction
is Revit to RAM Structural System (RAM SS), using BHoM's object model, engines,
and adapters wherever practical. Current work is discussion and basic compatibility
investigation, including whether any upstream fork is justified.

Treat the initial Revit-to-RAM SS qualification as one capability. Future adapters,
reverse transfers, result import, and synchronization are future scope. If the
user elects to deliver those as independent capabilities now, agree a capability
map before writing their specifications.

No product code, visible command, dependency installation, BHoM build, model
export, COM activation, or upstream modification has been performed. There is
no adjacent command SPEC to preserve: the strHUB pulldown was empty on inspection.

## Observed baseline

The extension checkout was clean before this discovery file was added.

| Component | Inspected evidence | Meaning |
| --- | --- | --- |
| Extension | Branch `dev.ram-push`, HEAD `5bb67c34b2c952ac60a938899e46627fca7a5c49` | Existing development branch retained. |
| Revit 2024 | Installed executable `24.3.60.12` | Available alternate host; not qualified here. |
| Revit 2025 | Installed executable `25.5.0.57`; `RevitNET.runtimeconfig.json` requests `net10.0` | Exact update/runtime matters, not just the Revit year. |
| Revit 2026 | Installed executable `26.5.0.55`; runtime config requests `net10.0` | User-selected first host; runtime integration remains unqualified. |
| Revit 2027 | Installed; runtime config requests `net10.0` | Outside the inspected BHoM Revit build configurations. |
| pyRevit | Version file `6.5.3.26176+2017` | Installed clone's version, not a live runtime assertion. |
| pyRevit attachment | User manifests for 2024/2025/2026 point to `IPY2712PR`; netfx for 2024, netcore for 2025/2026 | Preserve IronPython 2.7 command compatibility. Live assembly loading remains untested. |
| .NET | SDK `10.0.402`; .NET 8 and 10 runtimes installed | Toolchain available; BHoM dependencies still need provisioning. |
| RAM SS | Manager, Modeler, and registered DataAccess server report `25.00.02.42` | Exact target application version identified. |
| RAM COM | 64-bit registry contains CLSID `{831DA20F-FE64-4A33-B24F-25CEE81939DC}`, ProgID `RAMDataAccess.RamDataAccess1.1`, threading model `Apartment` | Expected coclass registration exists. This does not prove activation, licensing, API behavior, or export. |
| BHoM deployment | `C:\ProgramData\BHoM\Assemblies` absent; Revit/RAM reference checkout `Build` directories absent | Source references exist; a usable runtime deployment was not found at the inspected expected paths. |
| Local precedent | Startup Importer has `net48` / `net8.0-windows` compiled Revit/UI helpers and `netstandard2.0` core | A thin pyRevit adapter with compiled helpers fits established repository practice. Its success does not qualify BHoM. |

The installed COM server path is
`C:\Program Files\Common Files\Bentley\Engineering\RAMDataAccess_2_0\RamDataAccess.dll`.
The installed interop assembly was inspected with `ReflectionOnlyLoadFrom`, without
constructing any objects. It contains `RamDataAccess1`, `IRamDataAccess1`, and
`RamDataAccess1Class`; the coclass GUID matches the registration above. Resolving
the correct ProgID in the 64-bit inspection process succeeded without activation.
An initial guessed ProgID without the `1.1` suffix did not resolve; that was a
lookup error, not a missing RAM installation.

Sources are reference-only sibling checkouts under
`C:\Users\ai_lmadden\Dev\pyRevit\`. No upstream code was copied into this extension.

| Reference | Local commit inspected |
| --- | --- |
| `.ref.bhom.Revit_Toolkit` | `5cd34ccc523e18fddcad51105a1fa7b0ea81893c` (`main`, clean) |
| `.ref.bhom.RAM_Toolkit` | `a5746e25a49834fe01db6747c6520dba668b0c97` (`main`) |
| `.ref.bhom.Engine` | `d5e38ac46c953ef1083e218549b730e82a73d9f3` |
| `.ref.bhom.Adapter` | `99ed86d25278ec56c35dfb6e3a6c18f5f7d2e189` |

Public RAM `develop` resolved to `8dee79ffc8f149f4630fc72a4b2272447473d02d`
during research. Selected project/conversion files were checked against that
revision. Public develop declares assembly version 10.0; local RAM/Revit project
files declare assembly version 9.0 and file version 9.3. These are not one
automatically compatible dependency set. A coherent BHoM release/revision set
must be selected before qualification.

## Revit and BHoM integration findings

1. **BHoM can be reused from a code-based workflow.** Its core is not restricted
   to Grasshopper. The public Revit adapter communicates with an in-Revit adapter
   through a listener/socket route, and the inspected source also has a direct
   `InternalAdapter` route. That makes direct reuse from a pyRevit-hosted .NET
   layer a candidate, not a tested integration. The listener adapter constructor
   accepts `UIControlledApplication` and `Document`; the exact pyRevit hookup and
   lifetime still require investigation.
2. **Builds are Revit-specific.** Local `Revit_Core_Engine.csproj` and
   `Revit_Core_Adapter.csproj` target net48 for 2022-2024 and net8.0-windows for
   2025-2026. No 2027 configuration was found. The other Revit toolkit projects
   inspected target net472. A target-framework difference alone does not prove
   failure on .NET 10; a load/conversion test is required.
3. **Physical/analytical geometry policy is consequential.**
   `Revit_Core_Engine/Convert/Structure/FromRevit/Bars.cs` starts from a physical
   `FamilyInstance`. For 2023 onward it uses an associated `AnalyticalMember`
   curve when available, otherwise the physical location curve. This can produce
   mixed geometry provenance unless strHUB defines and reports the policy.
   The user has now required physical location lines exclusively; associated
   analytical curves must not supply export geometry.
4. **Useful identity data exists.** Conversion calls `SetIdentifiers`, attaching
   Revit identifiers including `UniqueId`. Preserve source document identity as
   well as element identity before claiming suitability for future round trips;
   an element number or BHoM GUID alone is not a synchronization contract.
5. **Use BHoM's schema and units.** BHoM's C# object model is the primary schema;
   JSON Schema is generated from it. Engines use SI units and adapters own
   conversion. The inspected Serialiser_Engine targets netstandard2.0 and
   provides JSON conversion. A versioned transfer package using that machinery
   is a candidate, but object/fragment reconstruction and schema validation do
   not establish engineering fidelity without tests.
6. **Upstream builds have deployment effects.** Revit projects have post-build
   copy commands targeting ProgramData and Revit add-in folders; other BHoM
   projects also target shared assembly folders. Do not run stock builds while
   claiming every output is confined to strHUB. A later isolated build must
   control these targets explicitly.

Primary references:

- [Revit toolkit at inspected commit](https://github.com/BHoM/Revit_Toolkit/tree/5cd34ccc523e18fddcad51105a1fa7b0ea81893c).
- [Revit adapter architecture](https://bhom.xyz/documentation/Guides-and-Tutorials/Coding-with-BHoM/Revit%20Toolkit/Revit%20Adapter%20Details/).
- [BHoM JSON Schema](https://bhom.xyz/documentation/BHoM_oM/JSONSchema/).
- [BHoM units](https://bhom.xyz/documentation/BHoM_oM/BHoM-Units-conventions/).
- [Autodesk's .NET transition notice](https://help.autodesk.com/view/RVT/2025/ENU/?caas=caas%2Fsfdcarticles%2Fsfdcarticles%2FRevit--Requirements-for-products-affected-by-the-Microsoft--NET-10-transition.html).

## RAM adapter: fidelity and compatibility findings

The [RAM adapter project](https://github.com/BHoM/RAM_Toolkit/blob/8dee79ffc8f149f4630fc72a4b2272447473d02d/RAM_Adapter/RAM_Adapter.csproj)
targets net472 and references `Interop.RamDataAccessLib_v15_x64` version 1.0.0,
with embedded interop types. The README names RAM SS v17 as known supported.
Neither that statement nor the installed COM registration establishes support
for RAM SS 25 or for loading the complete adapter dependency tree in Revit's CLR.

| Concern | Source behavior | Consequence for a first transfer |
| --- | --- | --- |
| Levels | Floor types created; stories at or below zero skipped | Explicit base datum and story mapping required. |
| Bars | Inclination selects beam or column; beams flattened to nearest story; columns get zero offsets | Restrict an initial proof to agreed horizontal beams and vertical columns. No brace fidelity assumption. |
| Sections | Section creation is an unimplemented ID-assignment stub; member gets `SectionProperty.Name` as RAM label | Verify each mapping against a real RAM catalogue and read back assigned sizes. |
| Materials | Material creation is similarly unimplemented; conversion distinguishes steel/concrete with fallback behavior | A material name crossing the boundary is insufficient proof of property fidelity. |
| Grids | Orthogonal X/Y paths; skew/circular TODOs; direct indexing into both directional lists | Do not assume arbitrary grid support. |
| Slabs/walls | Creation paths exist, with approximations/defaults; deck fallback can be `ASC 3W`; thin topping can become 2 inches after an error | Exclude from a minimal frame proof unless explicitly added and independently verified. |
| Loads | Creation paths for `UniformLoadSet` and `ContourLoadSet` | This is not broad load-case/load-combination support. |
| Updates/deletion | Bar update experimental; generic update reports success without action; delete stub | One-way creation does not establish round-trip synchronization. |
| Overall outcome | Individual conversions can warn, approximate, or partially fail | Success must include readback and a reconciled transfer report, not just a successful Push return. |

Pinned source evidence:

- [Bar creation](https://github.com/BHoM/RAM_Toolkit/blob/8dee79ffc8f149f4630fc72a4b2272447473d02d/RAM_Adapter/Create/Bar.cs).
- [Section creation](https://github.com/BHoM/RAM_Toolkit/blob/8dee79ffc8f149f4630fc72a4b2272447473d02d/RAM_Adapter/Create/SectionProperty.cs).
- [Material creation](https://github.com/BHoM/RAM_Toolkit/blob/8dee79ffc8f149f4630fc72a4b2272447473d02d/RAM_Adapter/Create/MaterialFragment.cs).
- [Surface properties](https://github.com/BHoM/RAM_Toolkit/blob/8dee79ffc8f149f4630fc72a4b2272447473d02d/RAM_Adapter/Create/SurfaceProperty.cs).
- [Experimental bar update](https://github.com/BHoM/RAM_Toolkit/blob/8dee79ffc8f149f4630fc72a4b2272447473d02d/RAM_Adapter/Update/Bar.cs).
- [Deletion stub](https://github.com/BHoM/RAM_Toolkit/blob/8dee79ffc8f149f4630fc72a4b2272447473d02d/RAM_Adapter/Delete/_Delete.cs).

Relevant open issues observed during research:
[section assignment #224](https://github.com/BHoM/RAM_Toolkit/issues/224),
[deck/floor assignment #216](https://github.com/BHoM/RAM_Toolkit/issues/216),
[push outcome/error handling #212](https://github.com/BHoM/RAM_Toolkit/issues/212),
and [missing levels #165](https://github.com/BHoM/RAM_Toolkit/issues/165).
These identify test targets; they do not prove the exact observed host reproduces them.

The active [RAMAdapter constructor](https://github.com/BHoM/RAM_Toolkit/blob/a5746e25a49834fe01db6747c6520dba668b0c97/RAM_Adapter/RAMAdapter.cs)
creates COM objects, can create a default `BHoM_Model.rss` in Bentley's ProgramData
data folder when a requested path is absent, and invokes sidecar cleanup. It is
not a read-only probe. Later write tests need a disposable, explicitly resolved
target and verified handling of the adapter's missing-path fallback.

## Options to evaluate, not accepted architecture

The reuse-first hypothesis is:

`pyRevit command -> BHoM Revit conversion -> BHoM objects -> strHUB validation/mapping -> BHoM RAM adapter -> RAM SS`

BHoM would own transferable engineering objects and available conversions.
strHUB would own user intent, supported-feature checks, source/target identity,
mapping policy, diagnostics, and orchestration. Retain a path for a different
target adapter without making RAM-specific objects the universal schema.

Two runtime placements remain open: calling the RAM adapter in-process from a
compiled helper, or using a separate Windows worker if legacy CLR/dependency/COM
requirements justify it. The BHoM Revit listener/socket route is another existing
integration mechanism to evaluate. A worker adds deployment and serialization
cost; in-process reuse adds assembly collision and host-lifetime risks. No choice
has been made and no new protocol has been designed.

**Fork recommendation, provisional:** first use pinned upstream dependencies
and configuration/wrappers. Consider a narrowly scoped maintained fork only for
a reproduced blocker that requires modifying upstream internals; keep changes
small and suitable for contribution upstream. The inspected repositories declare
LGPL-3.0 (source headers allow 3 or later). Before distributing dependencies or
modified binaries, review the exact licenses, notices, and corresponding source
requirements. No code has been vendored and no distribution conclusion is made.
[RAM license](https://github.com/BHoM/RAM_Toolkit/blob/8dee79ffc8f149f4630fc72a4b2272447473d02d/LICENSE).

## Decision tree and interview record

Settled by the user's request: DevSandbox destination; BHoM reuse preference;
Revit-to-RAM SS as the initial transfer direction; future multi-software and
round-trip intent.

### Round 1: settled choices

1. **Milestone accepted:** qualify a tiny agreed steel frame exported to a new
   RAM file, with transferred/skipped reporting and no Revit model changes.
2. **Source policy specified by the user:** use physical columns and beams,
   using their location lines. This is more specific than accepting BHoM's
   physical-to-analytical fallback behavior. Associated analytical geometry is
   excluded as an export geometry source.
3. **Version target accepted:** installed Revit 2026 `26.5.0.55` and RAM SS
   `25.00.02.42` first.

### Follow-up source inspection: physical location lines

At the pinned local Revit toolkit revision, `BarsFromRevit` unconditionally
tries the analytical association before the physical fallback. No physical-only
switch was found in the inspected settings. Its fallback
`Query/LocationCurve.cs` also does more than read a raw Revit location curve:
framing conversion can transform the axis and apply start/end extensions;
column conversion can apply column extensions; missing location data can fall
back to solid geometry. Those behaviors cannot silently define the user's
requested geometry policy.

Vertical columns can be point-located. The inspected BHoM column query derives
an axis from insertion X/Y and base/top level elevations plus offsets before
applying extensions. A proposed strHUB definition is to use that insertion and
constraint information to define the vertical line, without the later solid or
extension adjustments. Beam geometry uses the stored physical
`LocationCurve.Curve` directly. The user accepted this definition in round 2.

This is an identified behavior gap, not yet a reason to fork: an explicit
geometry extraction/composition layer may preserve BHoM's objects, other
conversion helpers, and RAM adapter while satisfying the requirement. The
implementation mechanism belongs in the later approved plan.

Evidence:
[BHoM location query](https://github.com/BHoM/Revit_Toolkit/blob/5cd34ccc523e18fddcad51105a1fa7b0ea81893c/Revit_Core_Engine/Query/LocationCurve.cs),
[BHoM bar conversion](https://github.com/BHoM/Revit_Toolkit/blob/5cd34ccc523e18fddcad51105a1fa7b0ea81893c/Revit_Core_Engine/Convert/Structure/FromRevit/Bars.cs),
and [Autodesk's Revit 2026 LocationPoint reference](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/8d81892a-7863-cbec-9148-a0311f3bf2b6.htm).

### Round 2: settled choices

4. **Location-line definition:** use beam `LocationCurve` endpoints directly;
   derive vertical column axes from insertion X/Y and base/top levels plus
   offsets. Ignore analytical geometry, solid extents, and end-extension
   adjustments. Accepted by the user.
5. **Proof contents:** manually select a one-story rectangular steel bay in the
   active document: four vertical columns and four straight horizontal beams,
   using standard AISC sections and the required Revit levels. Linked elements,
   braces, slabs, walls, loads, and analysis/design execution are excluded from
   this first proof. Accepted by the user.
6. **Fidelity policy:** block export before target writes if an included member
   cannot be represented faithfully or its RAM section mapping is unverified;
   report the reason instead of silently flattening, moving, or substituting it.
   Accepted by the user, with emphasis on reporting. This makes skipped or
   unsupported input explicit and prevents
   a partial or approximated model from being reported as a successful proof.
7. **Datum:** choose a Revit base level for RAM Z=0; preserve Revit internal X/Y
   and axes, translate export Z by the chosen base elevation, and record that
   transform. Apply the translation to export data only. Accepted by the user.

The seven answers establish the scope captured in [SPEC.md](SPEC.md). Its review
confirms shared understanding and exclusions before planning. The actual fixture
and section mapping values will be recorded with test evidence rather than
guessed here.

### Spec feedback: development file policy and unresolved comparisons

- The user accepted a new RAM file per run for initial development and explicitly
  requires reconsidering model reuse/update behavior in future scope.
- The user requested further discussion of the suggested 1 mm tolerance. It
  is not an accepted threshold and is not based on measured RAM precision.
  Distinguish numeric readback comparison from permission to move geometry or
  merge nearby nodes; the agreed physical-axis rule remains in force.
- The user requested an explanation of retaining failed output. The draft
  explains retaining only owned files that actually exist after writing starts,
  with failure diagnostics and no success/recovery guarantee. Retention versus
  cleanup remains a choice under discussion. Preflight-blocked runs still
  create no RAM model.

Runtime placement, dependency pins, isolated build commands, and any fork
decision remain technical questions for the approved planning/qualification
workflow. No implementation is authorized by this discovery document.

## What has and has not been verified

Verified through read-only source, file, manifest, assembly-metadata, and registry
inspection: baseline versions above, BHoM target declarations, RAM COM class
registration, and the listed conversion behaviors. Official web documentation
and selected current RAM source were also checked. Git executable access and
protected add-in manifests required the host's tool approval mechanism.

Not verified: BHoM build/restore, complete dependency closure, assembly loading
under pyRevit, Revit API calls through BHoM, COM activation/licensing, model
creation/save/reopen, section assignments, geometry/units fidelity, transfer
identity persistence, or any round trip. No live Revit process was observed
during the initial process check. No engineering acceptance has been claimed.
