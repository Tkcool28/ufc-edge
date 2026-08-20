# Raw Source Surface Inventory

Generated from files already committed under `data/raw/`. This is an acquisition/schema inventory, **not** a canonical field-selection decision.

| Source | Collection | Rows | Snapshot | Surface |
|---|---|---:|---|---|
| espn_mma | 20260820T123114Z |  | 20260820T123114Z |  |
| greco1899_ufcstats | ufc_event_details | 784 | 8e40eb945e11 | EVENT, URL, DATE, LOCATION |
| greco1899_ufcstats | ufc_fight_details | 8859 | 8e40eb945e11 | EVENT, BOUT, URL |
| greco1899_ufcstats | ufc_fight_results | 8859 | 8e40eb945e11 | EVENT, BOUT, OUTCOME, WEIGHTCLASS, METHOD, ROUND, TIME, TIME FORMAT, REFEREE, DETAILS, URL |
| greco1899_ufcstats | ufc_fight_stats | 41672 | 8e40eb945e11 | EVENT, BOUT, ROUND, FIGHTER, KD, SIG.STR., SIG.STR. %, TOTAL STR., TD, TD %, SUB.ATT, REV., … (+7) |
| greco1899_ufcstats | ufc_fighter_details | 4600 | 8e40eb945e11 | FIRST, LAST, NICKNAME, URL |
| greco1899_ufcstats | ufc_fighter_tott | 4601 | 8e40eb945e11 | FIGHTER, HEIGHT, WEIGHT, REACH, STANCE, DOB, URL |
| kaggle_pro_mma_fighters | binduvr/pro-mma-fighters | 5151 | v1 | url, fighter_name, nickname, birth_date, age, death_date, location, country, height, weight, association, weight_class, … (+10) |
| kaggle_pro_mma_fights | binduvr/pro-mma-fights | 10448 | v1 | url, event_title, organisation, date, location, match_nr, fighter1_url, fighter2_url, fighter1_name, fighter2_name, fighter1_result, fighter2_result, … (+5) |
| tidytuesday_ufc_rankings | 107ff6c70de0 |  | 107ff6c70de0 |  |
| ufc_com_official | athletes | 4160 | 20260820T173134Z | age, athlete_short_bio, broadcast_flag, changed, content_translation_outdated, content_translation_source, created, custom_name_override, default_langcode, dob, dod, don_best_id, … (+57)<br>rels: athlete_card_image, athlete_ranking, athlete_stat, athlete_status, athlete_type, attributes, fighting_style, gallery_content |
| ufc_com_official | events | 799 | 20260820T194553Z | changed, closed, computed_broadcast, content_translation_outdated, content_translation_source, created, cta_links, default_langcode, don_best_id, drupal_internal__nid, drupal_internal__vid, ds_switch, … (+47)<br>rels: event_status, event_type, fight_card_broadcast, fights, hero_buttons, image_event, image_hero, image_poster |
| ufc_datalab_scorecards | 3268146c0521 |  | 3268146c0521 |  |
| ufc_fightmetric_official | fight_roundboard | 374 | 20260820T123046Z | combined, drupal_internal__id, fightmetric_id, metatag, rank, round, statname, value |
| ufc_fightmetric_official | fight_stat | 57382 | 20260820T123046Z | back_ctl_time, body_sig_str_att, body_sig_str_land, body_str_att, body_str_land, clinch_body_str_att, clinch_body_str_land, clinch_head_str_att, clinch_head_str_land, clinch_leg_str_att, clinch_leg_str_land, clinch_sig_kick_att, … (+78) |

## Rules

- This file reports what sources expose; it does not authorize mappings by name similarity.
- Canonical mappings belong in `schemas/source_field_map_v0.json` and require semantic verification.
- Missing fields remain missing; a provider without a field does not imply zero.
- Raw provider vocabulary never becomes a downstream feature definition directly.
