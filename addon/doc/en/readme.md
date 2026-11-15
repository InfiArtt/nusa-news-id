# NusaNewsID

NusaNewsID reads news from Indonesian news sites in NVDA. It checks for new stories in the background, announces them, and shows whole articles in an accessible window, so you do not need a browser full of ads.

The add-on uses NVDA's language. This guide uses the English names of buttons and messages. The news itself is in Indonesian.

## Requirements

- NVDA 2026.1 or later.
- An internet connection.

## Sources and categories

There are ten categories: National, International, Technology, Politics, Economy, Sports, Entertainment, Disability, InfiArtt articles and InfiArtt knowledge base. Not every source has every category, because the add-on only follows sections that the site still updates.

- Antara, Kompas, Liputan6, Merdeka and CNN Indonesia: every category.
- Detik: every category except Politics.
- Republika: National, International, Technology, Economy, Sports and Disability.
- WinPoin, news about Windows and Microsoft: Technology.
- InfiArtt, the organization that makes this add-on: InfiArtt articles (from infiartt.com/posts) and InfiArtt knowledge base (guides from infiartt.com/kb). InfiArtt is always checked and cannot be turned off. The age rule below does not apply to InfiArtt: all its articles and guides are in the list, however old, and storage never removes them. Articles only InfiArtt members can read show their summary; open them in the browser and sign in to read them.

Stories come from a site's RSS feed when the feed is kept up to date, and from its category pages otherwise. Each story stays in the category it was listed under. Stories older than the storage period are skipped.

The Disability category has news about disability and people with disabilities. For sources without their own disability section, the add-on reads the disability tag page and keeps only stories whose title or summary has a word such as disabilitas, difabel, tunanetra, Tuli or kursi roda. Words are matched as whole words.

## Opening the news list

Press NVDA+Shift+slash anywhere. The news list opens on the newest story. You can change the key in the NVDA menu, Preferences, Input gestures, category NusaNewsID.

If the news list is already open, the same key moves the focus back to it.

## The news list

Every story is read in the same order: the title, then the source, category and time. For example:

"Sapaan Prabowo ke Jenderal Suyudi. Detik, National, 14 minutes ago. Unread."

- "Breaking." comes before the title only for breaking news.
- "Unread." comes at the end only for stories you have not opened or marked read.
- Times read "just now", "14 minutes ago" or "3 hours ago" for today's stories, and as a date and time after that, such as "13 November 2026, 20:00".
- If the site gives no publication time, the add-on uses the time it first found the story.
- For InfiArtt articles and guides, the author comes after the category, such as "InfiArtt, InfiArtt articles, by Rexya, 29 October 2026, 13:01."

The newest stories come first. The list shows 50 stories at a time, and you can change this number in the settings. The last item reads, for example, "Load 50 more stories". Press Enter on it to show the next stories.

Press Enter on a story to read it.

Above the list are these filters:

- Source (Alt+S): show one source only, or All. InfiArtt comes right after All.
- Category (Alt+T): show one category only, or All.
- Unread only (Alt+U): hide stories you have read.

Below the list are these buttons:

- Copy link (Alt+L): copies the web address of the selected story.
- Mark read (Alt+M): marks the selected story as read.
- Mark all read (Alt+A): marks every saved story as read.
- Refresh (Alt+R): checks for new stories now. NVDA says "Checking for new stories...", then, for example, "Done, 3 new stories." or "Done, no new stories."
- Donate (Alt+O): how to support the add-on's development.
- Close (Alt+C or Escape).

If the list is empty, for example because no story matches the filters, it has one line that says so.

When new stories arrive while the list is open, the list updates and the story you selected stays selected.

## Reading a story

The reader opens the story as a page that NVDA reads in browse mode, with the story's title as the window title. Use the arrow keys to read, H to move by heading, L by list and K by link. The story is marked as Indonesian, so if automatic language switching is on in NVDA, NVDA reads it with an Indonesian voice.

The top of the page has:

1. The title, as a level 1 heading.
2. The source and category, such as "Detik, category National". For InfiArtt, the next line names the author, such as "Written by Rexya".
3. The publication time, such as "Published 15 November 2026, 06:09". If the site gives none, this line reads "Found ..." with the time the add-on first found the story.
4. The story's web address.

Then comes the story, with the headings, lists, quotes and links of the original article. Ads, "baca juga" boxes, sidebars and copyright lines are left out. Images appear only when they have a description. Links open in your browser.

The first time you open a story, the add-on downloads its text, and NVDA says "Story loaded." when it is ready. The text is saved, so you can read the story again without the internet while it stays in storage. Opening a story also marks it read.

For low vision:

- Control+plus makes the text larger, Control+minus smaller, and Control+0 goes back to 100 percent. The size goes from 100 to 400 percent, and NVDA says it, such as "Text size 150 percent". The add-on keeps the size for the next story.
- The page uses the Windows colors, including contrast themes. Lines are well spaced and at most about 70 characters long, so large text still wraps without scrolling sideways.
- The focused button has a clear outline.

Buttons at the end of the page, which also work from anywhere in the page with their shortcut keys:

- Open in browser (Alt+B): opens the story on its website.
- Copy link (Alt+L): copies the story's web address.
- Copy story (Alt+S): copies the title and the text, without the details lines.
- Close (Alt+C or Escape): goes back to the news list.

If Windows cannot show web pages, the reader uses a plain text box with the same text.

## Announcements of new stories

The add-on checks for new stories every 5 minutes, and you can change the interval in the settings. The first check starts a few seconds after NVDA starts.

You can choose how new stories are announced:

- Number of new stories, the default: one message, such as "NusaNews: 5 new stories. Press NVDA+shift+/ to open them." The message names the key you use to open the news list, including a key you set in Input gestures.
- Title of each new story: the titles of all new stories in one message, such as "New from Detik: ...". With more than 5 new stories, NVDA gives the number instead.

Every announcement also appears on a braille display.

Breaking news means stories about disasters and emergencies. The add-on recognizes them by whole words in the title: gempa, tsunami, erupsi, meletus, banjir bandang, longsor, kebakaran hutan, bencana, darurat, evakuasi, peringatan dini, bom, teroris and "breaking news".

The first check after installing the add-on, or after deleting every saved story, does not announce stories one by one. It saves them as read, and NVDA says one message, such as "NusaNews: 450 stories loaded." A source with no saved stories yet, such as one you just turned on, is also saved quietly as read the first time.

## Quiet hours

During quiet hours, the add-on does not announce new stories or play a tone. It still saves them, and you can read them in the news list. If "Announce breaking news during quiet hours too" is checked, breaking news is still announced.

Quiet hours can pass midnight, for example from 22:00 to 06:00.

## Settings

Open the NVDA menu, Preferences, Settings, and choose the NusaNewsID category. From NVDA 2026.3, these settings are the same in every configuration profile.

- News sources to follow: a list of check boxes. Choose at least one source. InfiArtt is not in this list because it is always checked.
- Check for new stories every (minutes): 2, 5, 10, 15, 30, 60 or 120 minutes.
- Notifications group:
  - How to announce new stories: Number of new stories, or Title of each new story.
  - Play a tone when new stories arrive.
  - Announce breaking news during quiet hours too.
- Quiet hours group:
  - Use quiet hours.
  - Start and End: hours and minutes, such as 22:00 and 06:00. If a time is not valid, NVDA says which field to fix.
- Number of stories shown at a time: 20, 50 or 100.
- Reader text size (percent): 100 to 400 percent. Control+plus and Control+minus in the reader change it too.
- Storage group:
  - Keep stories for (days): 1 to 30 days. Older stories are removed after every check, except InfiArtt articles and guides.
  - Delete all saved stories: deletes every saved story and article text after you press Delete in the confirmation dialog. This cannot be undone.
- Skip security certificate checks: use this only if every connection fails because of a certificate problem on your computer. It makes the connections unsafe.
- Support and donations.

## Saved data

The add-on keeps its data in NVDA's settings folder, in a folder named nusaNewsID. The file nusaNewsCache.json holds the title, source, category, time and read status of each story. The articles folder holds the text of the stories you opened.

The add-on only connects to the news sites you chose. It does not send personal data anywhere.

## Troubleshooting

- No stories at all: check the internet connection, then press Refresh in the news list.
- One source never has new stories: the site may have changed its pages. Report it on the repository's issues page below.
- A story's text does not download: press Open in browser to read it on the website.

## Version history

The full history is in CHANGELOG.md in the repository https://github.com/InfiArtt/nusa-news-id.

## Author and license

NusaNewsID is made by Rexya Muhamad Rizki and developed with InfiArtt. Report problems and ideas at https://github.com/InfiArtt/nusa-news-id/issues.

The add-on is released under the GNU General Public License, version 2 or later.
