# WP-025 — Guest-only Gramps context for AI Research

The AI Research screen can search up to twelve Guest-visible people and load a
bounded preview of a selected person's events and immediate family links. It
uses a dedicated Gramps Guest account, not the owner credential. The bridge
accepts only the validated Gramps Web API 3.24 response contract and reads
fixed object routes. It never writes an accepted Gramps tree object.

The local model receives a tree event only when that event has a visible
Gramps source citation. The screen labels uncited tree entries as context and
labels any model interpretation as unverified. A citation's presence does not
prove that the linked source is an original, independent or correctly read
record. The separate research database remains the place for reviewed source
documents and observations.

The current imported tree has 1,629 people and no Gramps source or citation
objects. Consequently, selecting an Oldham person helps navigate the tree but
does not produce cited tree evidence for the model. No historical Oldham record
was added or identity match asserted in this work package.

For Cheshire, the interface offers manual leads to Cheshire BMD and Cheshire
Archives and Local Studies alongside the existing FreeBMD, FreeCEN, FreeREG
and National Archives leads. These links are **not searched by 24 Gen**. In
particular, FreeBMD's published terms prohibit programs from submitting
search parameters through its public search pages. Check each source's rights
before copying records; enter only reviewed, attributable extracts with clear
citations and keep possible family matches provisional.

The Windows cold-backup script now restricts the backup directory before it
writes private archive files. A verified backup and isolated restore test are
required before further release decisions. Do not commit `.env`, Guest
passwords, genealogy records or raw backup archives. The stacked pull request
remains draft and must not be merged merely because the local UI works.
