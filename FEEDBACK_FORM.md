# Friends-pilot feedback form

Two forms, five questions each, sent at end-of-week-1 and end-of-week-2
to the 3-5 friends running WordCounter Pro. Keep it short — longer forms
lose response rate fast in a pilot of this size.

## Where to host it

Either tool works; pick whichever you're already logged into.

- **Google Forms** (`https://forms.google.com`) — free, aggregates to
  Google Sheets automatically, easy to re-send with a pre-filled URL.
- **Tally** (`https://tally.so`) — free tier is generous, prettier
  default UI, no Google account needed to fill it out.

Create **one form per week** so you can compare week-1 vs week-2
responses side by side.

Plug the shareable form URL into the email template below, and also
paste it into the app's `Help → Send Feedback...` prompt when you
distribute the build (it's not auto-wired — just mention it in the
email).

---

## Week 1 — questions

Title: **WordCounter Pro — Week 1 feedback**

Intro text: *"You've had WordCounter for a week. 5 questions, ~2
minutes. No right answers — blunt feedback is the most useful thing."*

1. **How many days this week did you actually have WordCounter
   running while you wrote?**
   (multiple choice)
   - 0 days
   - 1-2 days
   - 3-4 days
   - 5-6 days
   - Every day

2. **What did you try to use it for?**
   (checkboxes, pick all that apply)
   - Journaling / morning pages
   - Fiction / creative writing
   - Work docs (memos, reports)
   - Note-taking / Zettelkasten
   - Newsletter / blog posts
   - School / research papers
   - Other (short text)

3. **If it felt broken or wrong at any point, what happened?**
   (paragraph, optional)

4. **Did the privacy model (only tracks inside writing apps, never
   sends anything anywhere) feel believable to you?**
   (multiple choice)
   - Yes, I trust it
   - Mostly, but I had a concern (please say what in Q3)
   - Not really
   - I didn't think about it

5. **If I asked you to pay $5/month for this a year from now, would
   you?**
   (multiple choice)
   - Yes
   - Maybe — depends on what's added
   - No

---

## Week 2 — questions

Title: **WordCounter Pro — Week 2 wrap-up**

Intro text: *"Final round. 5 questions, ~2 minutes. Honest > kind."*

1. **Compared to week 1, did you use it more, less, or about the
   same?**
   - More
   - About the same
   - Less
   - I stopped using it (please say why in Q5)

2. **What's the single most annoying thing about using it today?**
   (paragraph)

3. **If you could add one feature that would make you keep using it,
   what is it?**
   (paragraph)

4. **Who else in your life would benefit from this?**
   (short text — names, types of people, "nobody", all valid)

5. **Anything else — venting welcome:**
   (paragraph, optional)

---

## Email template to accompany each form

Subject line week 1: *"2 minutes — did WordCounter work for you this week?"*

Subject line week 2: *"Last ask — 2-minute WordCounter wrap-up"*

Body:

```
Hey {name},

Quick check-in on the WordCounter pilot. 5 questions, ~2 minutes:

{FORM_LINK}

Most useful thing you can give me: blunt feedback, even if it's "I
forgot about it after day 2". That's the signal I need.

(As a reminder, you can also hit Help → Send Feedback inside the app
any time.)

Thanks,
{you}
```

## What to do with the results

- Week 1: fix the top 1-2 bugs / annoyances that show up in Q3.
- Week 2: look at Q5 on the Week 1 form + Q1 on the Week 2 form. If
  fewer than half the pilots are still using it daily after 2 weeks,
  **do not** ship a paid v1 yet — iterate on the top complaint first.
- If retention is there, the Q3/Q5 answers give you the roadmap for
  the Public Beta milestone.
