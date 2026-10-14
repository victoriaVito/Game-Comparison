# Royal Match Missing-Capture Public-Source Search

**Checked:** 2026-10-13
**Status:** Candidate metadata only; no replacement image acquired.

## Result

The local archive manifest records 412 missing captures between levels 2 and 13,500. Level 1 is also absent, although it is outside the manifest's declared range, for 413 missing levels total.

The public-source search catalog contains 101 distinct YouTube video references. Each reference was rechecked through YouTube oEmbed for a video type, a non-empty title, and a non-empty author. The recorded level-range endpoints were also checked against the returned title. Comparing those title-claimed ranges with the manifest gaps yields a metadata lead for all 413 missing level numbers:

| Measure | Result |
|---|---:|
| Missing Royal Match level numbers | 413 |
| Missing numbers with a title-matched source lead | 413 |
| Missing numbers without a title-matched lead in this search | 0 |
| Distinct video metadata records | 101 |
| New image captures obtained | 0 |

Level 1 has a lead in the video titled `Royal Match Level 1 - 10 Gameplay Walkthrough`. The 412 manifest gaps are:

| Missing range | Levels |
|---|---:|
| 299-300 | 2 |
| 3776-3785 | 10 |
| 4341-4355 | 15 |
| 4509-4510 | 2 |
| 4541-4555 | 15 |
| 4931-4945 | 15 |
| 5411-5445 | 35 |
| 5561-5575 | 15 |
| 5706-5720 | 15 |
| 6161-6175 | 15 |
| 6541 | 1 |
| 6671-6690 | 20 |
| 6756-6776 | 21 |
| 6971-6975 | 5 |
| 6991-7005 | 15 |
| 7086-7105 | 20 |
| 7286-7310 | 25 |
| 7486-7510 | 25 |
| 7621-7635 | 15 |
| 8096-8100 | 5 |
| 8116-8130 | 15 |
| 8496 | 1 |
| 8631 | 1 |
| 8751-8775 | 25 |
| 9051-9070 | 20 |
| 9846-9850 | 5 |
| 9859 | 1 |
| 10646 | 1 |
| 11565-11566 | 2 |
| 12451-12500 | 50 |
| **Manifest total** | **412** |

The per-video catalog, including exact oEmbed title, author, claimed range, video URL, and metadata endpoint, is `missing-capture-public-sources.csv`. Its ranges are discovery leads derived from titles, not claims that every video actually shows each named level.

## Terms and next gate

The [YouTube Terms of Service](https://www.youtube.com/t/terms) state that users may view or listen to content for personal, non-commercial use and may display videos through YouTube's embedded player. The terms also restrict reproducing, downloading, or otherwise using content unless specifically permitted by the service, authorized in writing by YouTube and applicable rights holders, or permitted by law. They separately restrict automated access, subject to stated exceptions such as public search engines operating under YouTube's `robots.txt`, written permission, or applicable law.

Whether the prior oEmbed metadata checks fall within an authorized access method has not been determined here. Do not extend direct automated metadata collection or access the video media until the method and applicable terms are confirmed. A public title is not evidence that an uploader has granted permission to reuse footage or screenshots.

## Search for explicitly reusable sources

A public web search for sources with explicit download and reuse terms found Royal Match items in the [Wikimedia Commons category](https://commons.wikimedia.org/wiki/Category:Royal_Match). The official Commons API lists five files in the category. Its file metadata identifies [Royal Match Level 1300 Bonus Level.png](https://commons.wikimedia.org/wiki/File:Royal_Match_Level_1300_Bonus_Level.png) and [Royal Match Level 2102.png](https://commons.wikimedia.org/wiki/File:Royal_Match_Level_2102.png) as level images under CC BY-SA 4.0 and includes a VRT permission-confirmed notice. Both level numbers are outside the 413 missing levels, so neither fills an archive gap. The other category entries are generic gameplay or promotional images, not identified as one of the missing levels.

The YouTube page for [Royal Match - Level 291 - Level 300 by VinMat's Games](https://www.youtube.com/watch?v=ZKHMYAkO1vU) was opened in the browser to verify its visible description and chapters. It lists level 299 at 21:19 and level 300 at 24:45, making it a relevant visual lead for those two missing levels. The page did not show an explicit reuse license. This link and the chapter times are saved as a research lead, not as permission to download or extract frames. No media was downloaded.

## Limits

This was a metadata-only search. No video was opened or downloaded, no frame was extracted, and no screenshot was added to the archive. A title does not establish that the video is available, that a specific level appears in its footage, that a usable frame exists, or that reuse is permitted. Thus the local capture count is unchanged and all 413 levels remain missing in the archive.

The zero in “without a title-matched lead” means only that every missing number is covered by at least one title-claimed range in this catalog. It does not establish that other public sources do not exist. Reviewing or acquiring media, and saving or distributing screenshots, requires a confirmed permitted access method and appropriate rights or another applicable legal basis.
