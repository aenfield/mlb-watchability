# Score update notes

This file has notes on when and how I changed the calculation of the NERD scores, in case it's useful in the future, like when I do further analysis.

If I recall correctly, I didn't change the score calcs from when I started publishing - first .md file published to the blog is dated 7/21/2025 - through 8/1/2025. (I changed the calcs before 7/21, as I was experimenting, but wasn't publishing anything at that time.)

## Changes

- 8/2/2025 - For purposes of gNERD score, pitchers with no data are now treated as if they have a pNERD of five. Before this change the calc was doing an average of just a single score (assuming the other pitcher had a score), which overemphasized that single pitcher's contribution to watchability. The five number is a good midpoint - it's very close to the mean and median pNERD over ~175 games. Practically, sometimes pitchers with no data are AAA fill-in call-ups, and will likely be bad (and an actual zero would be better), while other times pitchers with no data are things like stars returning from injuries (and w/o the requisite 20 IP and 1 GS) (where a score higher than five would be better). When I update historical data, I probalby want to avoid combining data from before and after this change, for gNERD (doesn't matter for the pNERD scores because they individually don't change - I just use five in the gNERD calc, not change the reported pNERD score - and of course tNERD is unaffected), because of cases like the 8/3 ATL @ CIN game, with a no data ATL pitcher vs Chase Burns and his 14.2 pNERD. Before the change, the gNERD pitching component would have been 14.2, and now it's 9.6 (avg of 14.2 and 5), and this reduces the gNERD from the 18.8 it would have been to 14.2.
