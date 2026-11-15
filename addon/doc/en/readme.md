# NusaNews - Indonesian News Reader for NVDA

The NusaNews add-on allows you to monitor and read the latest news directly and accessibly from various leading news portals in Indonesia using the NVDA screen reader. Featuring a robust **Offline Reader Mode**, you can read full article bodies offline inside a comfortable, screen-reader friendly text box without opening external web browsers which are often cluttered with advertisements, overlays, and accessibility barriers.

## Key Features

*   **Single Keyboard Shortcut**: Press `NVDA+Shift+/` from anywhere to summon the main news reader dialog.
*   **Offline Reader Mode**: Open and read full news articles offline inside a multi-line, read-only text control. Read articles line-by-line or paragraph-by-paragraph using standard screen review arrow keys.
*   **9 Popular News Sources**:
    *   *General News*: Detik.com, Kompas.com, Antara News, Republika, Liputan6, Merdeka.com, and CNN Indonesia.
    *   *Technology News*: WinPoin (Windows/Microsoft news) and MacPoin (Apple/Mac news).
*   **Structured Categories**: Nasional, Internasional, Teknologi, Politik, Ekonomi, Olahraga, Entertainment, and Disabilitas.
*   **Disability Topic Filtering**: When selecting the "Disabilitas" category, the add-on automatically filters articles from all portals using a comprehensive list of localized disability-related keywords. This ensures only articles highly relevant to disability issues in Indonesia are shown.
*   **Smart Notification System**:
    *   *Digest*: Announces the number of new articles fetched during background polling cycles.
    *   *Immediate*: Speaks individual article titles as they are fetched (up to a maximum of 5 to prevent speech flooding).
*   **Do Not Disturb (Quiet Hours)**: Silences automatic news notifications during configurable hours (e.g. at night) so your rest is never interrupted.
*   **Display Limits & Pagination**: Restricts the initial number of news items displayed (20, 50, or 100) to keep dialog loading instantaneous, with an incremental `-- Muat Lebih Banyak --` (Load More) item at the bottom of the list to fetch more articles on the fly and focus automatically on the first new item.
*   **Persistent Local Cache**: Downloaded article contents are saved locally for instant retrieval.
*   **Bypass SSL Verification**: An emergency fallback option to skip SSL certificate verification if your local network connection encounters certificate validation errors.

---

## Usage Guidelines and Keyboard Shortcuts

### 1. Main News Reader Dialog
To open NusaNews, press **`NVDA+Shift+/`** from anywhere. The dialog will open and place focus directly on the news list box.
*   **Navigating the News**: Use **Up Arrow** and **Down Arrow** keys to select an article from the list.
*   **Reading Articles**: Press **Enter** or double-click on a selected article to open the offline **Reader Mode**.
*   **Copy Link (Alt+C)**: Copies the selected news article URL to the clipboard.
*   **Mark Read (Alt+D)**: Marks the selected news item as read (removing the `[Baru]` prefix).
*   **Mark All Read (Alt+M)**: Marks all currently listed news items as read.
*   **Refresh (Alt+S)**: Triggers a manual background check for new articles from all enabled sources immediately.
*   **Copy Link (Alt+L)**: Copy the URL of the selected news.
*   **Close Dialog (Alt+T or Escape)**: Closes the NusaNews dialog and returns to your previous application.
*   **Filtering by Source and Category**: Use the **Tab** key to move to the Source or Category filter dropdowns, and use the **Arrow** keys to change selections. The news list will update instantly.

### 2. Offline Reader Mode Dialog
When you open an article, the offline reader dialog displays a read-only text control containing the cleaned text. NVDA will automatically focus on this text control so you can start reading immediately.
*   **Reviewing Text**: Use standard text review keys (such as **Down Arrow**, **Up Arrow**, **Page Down**, etc.) to read the article.
*   **Open in Browser (Alt+B)**: Opens the original article webpage in your default web browser.
*   **Copy Link (Alt+L)**: Copies the current news article URL to the clipboard.
*   **Copy (Alt+S)**: Copies the full article text (including title and metadata) to the system clipboard.
*   **Close Reader (Alt+T or Escape)**: Closes the reader dialog and returns you to the main news list.

---

## Configuring Settings

You can customize the add-on settings through NVDA's Preferences:
1.  Press **`NVDA+N`** to open the NVDA Menu.
2.  Go to **Preferences** -> **Settings...**
3.  In the Category list on the left, find and select **nusaNewsID**.
4.  Use **Tab** to navigate through the following configuration controls:

*   **Active News Sources**: Check or uncheck news portals (Detik, Kompas, Antara, Republika, Liputan6, Merdeka, CNN Indonesia, WinPoin, MacPoin) to enable/disable them.
*   **Refresh Interval (minutes)**: Select how frequently the add-on polls for updates in the background (2, 5, 10, 15, 30, 60, or 120 minutes).
*   **Notification Mode**:
    *   *Digest*: NVDA speaks a summary count of new articles (e.g. *"NusaNews: 5 new articles available"*).
    *   *Immediate*: NVDA announces individual article titles in succession.
*   **Play a notification tone when there is new news**: Check to play a short beep sound whenever new news is fetched.
*   **Prioritize breaking news**: If enabled, articles labeled as breaking news are always announced immediately, overriding the general notification mode.
*   **Enable Jam Sunyi (Do Not Disturb)**: Check to silence automatic voice notifications during specified hours.
*   **Quiet Hours Start / End (HH:MM)**: Enter start and end times in 24-hour format (e.g. start `22:00` and end `06:00`).
*   **Bypass SSL Verification**: Check this option if you encounter SSL certificate validation errors from news sites (recommended to keep unchecked unless necessary).
*   **Initial Display Limit**: Set the initial number of news items loaded in the list (20, 50, or 100) to keep the interface fast.
*   **Cache Retention Limit (Days)**: Select how long downloaded article text should remain cached on disk (1 to 30 days). Expired cache items are cleaned up automatically when NVDA starts.
*   **Clear All News Cache**: Click this button to wipe all locally stored cache immediately. A confirmation dialog will appear.

---

## Version History

The full history is in CHANGELOG.md in the repository https://github.com/InfiArtt/nusa-news-id.

---

## Contributors
*   **Rexya Muhamad Rizki** (Lead Developer)
*   **NusaNews ID Team**
*   Built specifically for the blind and screen reader community in Indonesia.
