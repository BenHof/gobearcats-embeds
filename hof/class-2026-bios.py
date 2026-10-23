#!/usr/bin/env python3
"""Write the fuller Class of 2026 biographies into every dashboard variant and the review manifest.

    python3 hof/class-2026-bios.py

Each biography is drawn only from the inductee's official gobearcats.com Hall of Fame announcement
(the record's gb_url). The same text goes into all seven dashboard files, which verify-content.py
requires to agree, and into content-review-2026-10-23.json, whose `additions` are the expected
2026 records. Re-running is harmless.
"""
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PREFIX = "  const DATA = "
REVIEW = os.path.join(HERE, "content-review-2026-10-23.json")
ENHANCED_AT = "2026-10-23"

BIOS = {
    "Connor Barwin": (
        "Football and basketball letterwinner from Detroit. As a senior defensive end in 2008, Barwin led the BIG EAST with "
        "11.0 sacks, added 15 tackles for loss and a single-season program-record three blocked kicks, and earned First Team "
        "All-BIG EAST and Sports Illustrated honorable mention All-America honors. Before moving to defense he caught 53 passes "
        "for 692 yards and six touchdowns as a three-year tight end, and he played 34 games for UC men's basketball. A 2009 "
        "second-round pick of the Houston Texans, he played 10 NFL seasons and earned Pro Bowl and All-Pro honors in 2014."
    ),
    "Loretta Blaut": (
        "High jumper for Cincinnati from 2015 to 2019 and among the most decorated women in Bearcat track and field history. "
        "Blaut earned six All-America honors, five on the first team, the most by a UC female athlete, and won five AAC titles. "
        "She was NCAA runner-up indoors and outdoors in 2018, losing the indoor title only in a seven-round jump-off, and set "
        "school, meet, conference and facility records at 1.88 meters at the 2018 AAC Outdoor Championships before winning "
        "bronze for Team USA at the NACAC Championships."
    ),
    "Christy Hoffman": (
        "Goalkeeper for Cincinnati from 1997 to 2001 and the program's career leader in shutouts (32.5) and goalkeeper wins (59). "
        "In 2001 she set single-season records for goals-against average (0.58), wins (20) and shutouts (14) and was named "
        "Conference USA Defender of the Year and First Team All-Conference. She guided UC to two NCAA Tournaments, including "
        "the program's first Sweet Sixteen, the 2001 C-USA regular-season title and C-USA Tournament titles in 1997 and 2001, "
        "and was a CoSIDA Academic All-American."
    ),
    "Bob Huggins": (
        "Cincinnati's all-time winningest men's basketball coach with 399 victories from 1989 to 2005. Huggins led the Bearcats "
        "to 14 NCAA Tournaments, beginning with the 1992 Final Four, plus three Elite Eights, four Sweet Sixteens, eight league "
        "tournament titles and 10 regular-season conference championships. His 1999-2000 team spent 12 weeks ranked No. 1, "
        "nine of his players earned Associated Press All-America honors, and he was inducted into the Naismith Memorial "
        "Basketball Hall of Fame in 2022."
    ),
    "Jason Kelce": (
        "Walk-on linebacker in 2006 who became a three-year starter on Cincinnati's offensive line from 2008 to 2010 and a "
        "two-time All-BIG EAST selection. Kelce was the 2006 Scout Team Defensive MVP and helped UC win back-to-back "
        "conference championships and play in the 2008 Orange Bowl and 2009 Sugar Bowl. In 13 seasons with the Philadelphia "
        "Eagles he made six All-Pro teams and seven Pro Bowls, won Super Bowl LII and set the franchise record with 156 "
        "consecutive regular-season starts."
    ),
    "Mike Kinnett": (
        "Four-year starter at first base from 1984 to 1987 and UC's career batting average leader at .372. Kinnett hit .407 "
        "in 1985, one of five Bearcats ever to hit .400 in a season, and was a two-time all-conference pick in the Metro "
        "Conference, hitting .388 with career highs of seven home runs and 40 RBI in 1986. He ranks among UC's career leaders "
        "in hits (236), doubles (52) and total bases (362), and struck out only 51 times in 635 at-bats."
    ),
    "Wayne Mason": (
        "Hurdler for Cincinnati from 1977 to 1980 and one of the most decorated athletes in Bearcat track and field history. "
        "Mason was a First Team All-American in the outdoor 110-meter hurdles in 1980, competed at four NCAA Championships and "
        "finished fifth at the 1980 Olympic Trials, setting the school record of 13.60 seconds that year. He also holds UC's "
        "indoor 55-meter hurdles records, 7.1 hand-timed and 7.34 fully automatic, and ran on the 4x200-meter relay that set "
        "a school record in 1977."
    ),
}


def source_fields(record):
    return {"bio": BIOS[record["name"]], "bio_source": "gobearcats.com",
            "bio_source_type": "official_hall_of_fame_class_article",
            "bio_source_urls": [record["gb_url"]], "bio_enhanced_at": ENHANCED_AT}


def main():
    for path in sorted(glob.glob(os.path.join(HERE, "uc-hof-dashboard*.js"))):
        lines = open(path, encoding="utf-8").read().split("\n")
        idx = next(i for i, l in enumerate(lines) if l.startswith(PREFIX))
        data = json.loads(lines[idx][len(PREFIX):-1])
        hits = [r for r in data["inductees"] if r["name"] in BIOS and r["year"] == 2026]
        if len(hits) != len(BIOS):
            raise SystemExit(f"{os.path.basename(path)}: found {len(hits)} of {len(BIOS)} Class of 2026 records")
        for r in hits:
            r.update(source_fields(r))
        lines[idx] = PREFIX + json.dumps(data, ensure_ascii=True, separators=(",", ":")) + ";"
        open(path, "w", encoding="utf-8").write("\n".join(lines))
        print(f"{os.path.basename(path)}: {len(hits)} biographies")

    review = json.load(open(REVIEW))
    hits = [a for a in review["additions"] if a["name"] in BIOS]
    if len(hits) != len(BIOS):
        raise SystemExit(f"review manifest: found {len(hits)} of {len(BIOS)} additions")
    for a in hits:
        a.update(source_fields(a))
    with open(REVIEW, "w") as f:
        json.dump(review, f, indent=2)
        f.write("\n")
    print(f"review manifest: {len(hits)} additions")


if __name__ == "__main__":
    main()
