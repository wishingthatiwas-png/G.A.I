# G.A.I. Development Data Preservation Policy

Date: 2026-10-06
Status: ACTIVE PROJECT RULE

## Rule

Development documentation and project evidence are historical data.

Do not delete development documents. Do not replace historical documents with newer content.

When something becomes obsolete:
1. Mark it: ARCHIVED — NOT NEEDED FOR CURRENT BUILD.
2. Keep the original file intact.
3. Create the new version as a new dated/versioned document.
4. Update the active plan to point to the current document.
5. Periodically bundle archived documents into ZIP archives.
6. Keep archives available for audit, comparison, rollback and research history.

## Applies to
- audits
- TODO/build plans
- architecture documents
- research notes
- experiment reports
- snapshots
- test results
- design decisions
- implementation notes
- generated development documentation

## Versioning
Prefer names such as DOCUMENT_NAME_YYYY-MM-DD.md or DOCUMENT_NAME_vN.md.
Never silently overwrite an existing historical version.

## Archive marking
Archived documents should contain a short status header and identify the document that supersedes them when applicable.

## ZIP archives
Archived development documents may be bundled into dated ZIPs such as archive/development_docs_YYYY-MM-DD.zip.
The ZIP is an additional copy. Original files remain unless a separate explicit archival-storage policy is created.

## Current active documents
The active build plan, current TODO and current architecture documents should point to the latest version.
Historical audits remain evidence even after their recommendations are completed.

## Safety principle
No project history is disposable by default.
If storage becomes a problem, archive and compress first. Do not delete project evidence merely to keep the working directory clean.