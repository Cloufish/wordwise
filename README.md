# Wordwise

An Anki add-on for language learners. For each note, it can fill in:

1. A **frequency** field — how common the word is, looked up in an offline frequency list.
2. An **Image** field — a photo fetched from [Pexels](https://www.pexels.com/api/) to help memorize the word.
3. A **Gender** field — the noun's grammatical gender, looked up live on Wiktionary
   (optional; German, French, Spanish, and Portuguese are supported).

Field mapping is configurable per Note Type, so it works with any deck layout.

## Setup

1. **Get a frequency list.** Download the list for your target language from
   [hermitdave/FrequencyWords](https://github.com/hermitdave/FrequencyWords)
   (e.g. `content/2018/en/en_50k.txt` for English) and save it somewhere on disk.
2. **Get a Pexels API key.** Sign up for a free key at https://www.pexels.com/api/.
3. **Install the add-on.** Copy (or symlink) the `wordwise/` folder into your Anki
   `addons21` directory (find it via Anki: Tools ▸ Add-ons ▸ View Files), then restart Anki.
4. **Configure it.** Open the Wordwise settings dialog either via the main Anki
   window's **Tools ▸ Wordwise Settings…** menu item, or via **Tools ▸ Add-ons**
   → select "wordwise" in the list → **Config** button (both open the same dialog).
   - Paste your Pexels API key.
   - **Overwrite existing Frequency/Image field content when fetching**: off by
     default (fetching only fills in blank fields). Turn it on to re-fetch and
     replace values that are already there — this applies globally, to both the
     editor button and the Browser bulk action.
   - Click **Add…** to create a profile: pick a Note Type, then the field that holds
     the word, the field frequency should be written to, the field the image should
     be written to, and the frequency list file from step 1.
   - Optional: **Image search field** lets you search Pexels using a different field
     than the word field — useful since Pexels tends to return better results for
     English queries. E.g. keep "Word" (German) for frequency lookup, but set
     Image search field to an "English" translation field so the image search
     uses the English word instead. Leave it as "(same as Word field)" to search
     with the same word used for frequency.
   - Optional: **Gender field** + **Gender language** fetch the noun's grammatical
     gender by looking up the Word field on that language's Wiktionary edition
     (`de`/`fr`/`es`/`pt.wiktionary.org`). Leave Gender field as
     "(none — don't fetch gender)" to skip this entirely. The value written is the
     full English gender name — `masculine`, `feminine`, or (German only) `neuter`
     — e.g. `masculine/neuter` for the rare German noun with two valid genders.
     If the word has a Wiktionary page but isn't a noun there (a verb, adjective,
     ...), the field is filled with `not-applicable` instead of being left blank.
     Only these 4 languages are supported: other Wiktionary editions (Russian,
     Italian, Dutch, Polish, ...) mark gender in ways too inconsistent to parse
     reliably. A genuine lookup failure (no Wiktionary page found, network error)
     leaves the field blank and reports a specific reason rather than guessing.
   - You can add one profile per Note Type/language.

   To color a card's background by gender, add to the card template:
   ```html
   {{#Gender}}<div class="card {{Gender}}">{{/Gender}}
   ...your existing card content...
   </div>
   ```
   and to its CSS:
   ```css
   .card.masculine { background-color: #cfe8ff; }
   .card.feminine { background-color: #ffd6e0; }
   .card.neuter { background-color: #d9ffd6; }
   ```

## Usage

- **Single note**: while editing a note, click the **WW** button in the editor toolbar.
- **Multiple notes**: in the Browser, select the notes, then use
  **Notes ▸ Wordwise: Fetch Frequency, Image & Gender**.

By default, fields that already have content are left untouched — fetching only
fills in blanks. Enable **Overwrite existing Frequency/Image field content** in
Wordwise Settings to always re-fetch and replace instead.

## Notes

- Frequency lookup is fully offline; if a word isn't in your list file, the frequency
  field is left blank.
- Image search requires network access and a valid Pexels API key.
# wordwise
