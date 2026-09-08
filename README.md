# Wordwise

An Anki add-on for language learners. For each note, it can fill in:

1. A **frequency** field — how common the word is, looked up in an offline frequency list.
2. An **Image** field — a photo fetched from [Pexels](https://www.pexels.com/api/)
   (falling back to [Pixabay](https://pixabay.com/api/docs/) if Pexels finds nothing)
   to help memorize the word.
3. A **Gender** field — the noun's grammatical gender, looked up live via
   [freedictionaryapi.com](https://freedictionaryapi.com/) (optional; works for any
   language that API covers, not just a fixed list).

Field mapping is configurable per Note Type, so it works with any deck layout.

## Setup

1. **Get a frequency list.** Download the list for your target language from
   [hermitdave/FrequencyWords](https://github.com/hermitdave/FrequencyWords)
   (e.g. `content/2018/en/en_50k.txt` for English) and save it somewhere on disk.
2. **Get image API keys.**
   - **Pexels** (primary): sign up for a free key at https://www.pexels.com/api/.
   - **Pixabay** (fallback, optional but recommended): sign up for a free key at
     https://pixabay.com/api/docs/ (the key is shown right on that docs page once
     logged in). Used automatically when Pexels finds nothing for a word.
   - Gender lookup needs no key — freedictionaryapi.com is used as-is.
3. **Install the add-on.** Copy (or symlink) the `wordwise/` folder into your Anki
   `addons21` directory (find it via Anki: Tools ▸ Add-ons ▸ View Files), then restart Anki.
4. **Configure it.** Open the Wordwise settings dialog either via the main Anki
   window's **Tools ▸ Wordwise Settings…** menu item, or via **Tools ▸ Add-ons**
   → select "wordwise" in the list → **Config** button (both open the same dialog).
   - Paste your Pexels API key and (optionally) your Pixabay API key.
   - **Overwrite existing Frequency/Image field content when fetching**: off by
     default (fetching only fills in blank fields). Turn it on to re-fetch and
     replace values that are already there — this applies globally, to both the
     editor button and the Browser bulk action.
   - Click **Add…** to create a profile: pick a Note Type, then the field that holds
     the word, the field frequency should be written to, the field the image should
     be written to, and the frequency list file from step 1.
   - Optional: **Image search field** lets you search for images using a different
     field than the word field — useful since Pexels/Pixabay tend to return better
     results for English queries. E.g. keep "Word" (German) for frequency lookup,
     but set Image search field to an "English" translation field so the image
     search uses the English word instead. Leave it as "(same as Word field)" to
     search with the same word used for frequency.
   - Optional: **Gender field** + **Gender language** fetch the noun's grammatical
     gender by looking up the Word field via freedictionaryapi.com. Gender language
     is a free-text ISO 639-1/639-3 code (e.g. `de`, `fr`, `es`, `ja`, `ru`) — any
     language that API covers works, since the same lookup logic applies uniformly
     regardless of language. Leave Gender field as "(none — don't fetch gender)" to
     skip this entirely. The value written is the gender tag as reported by the
     dictionary — `masculine`, `feminine`, or `neuter` — joined with `/` for the
     rare word with more than one (e.g. `masculine/neuter`). A word that isn't a
     noun, or a language with no grammatical gender at all, simply won't find a
     gender tag; the field is left blank and a specific reason is reported rather
     than guessing.
   - You can add one profile per Note Type/language.

   To color a card's background by gender, add to the card template:
   ```html
   {{#Gender}}<div class="card {{Gender}}">{{/Gender}}
   ...your existing card content...
   </div>
   ```
   and to its CSS:
   ```css
.card {
  --bg-main-color: #f4f1de;
  --bg-title-color: #e07a5f;
	--bg-box-color: #8f5d5d;
	
	--targetLang-color: #9b2f40;
	--targetLang-font: sans-serif;
	--nativeLang-color: #3D405B;
	--nativeLang-font: sans-serif;

  --border-main-color: #8f5d5d;
  --border-box-color: #8f5d5d;

  --text-main-color: #eee5e9;
  --text-title-color: #ffffff;
  --text-box-color: #eee5e9;

  --alt-color: #9c5561;

  font-family: sans-serif,Menlo, Monaco;
  font-size: 1rem;
  background-color: var(--bg-main-color);
  color: var(--text-main-color);
  margin: 8px;

  --border-main-color: #4f4944;
  background-color: #6b625c; /* warm neutral gray — deliberately desaturated */
}



.card.masculine {
  --border-main-color: #2f4759;
  background-color: #3e5c76; /* muted slate blue — masculine */
}
.card.feminine {
  --border-main-color: #7a2e40;
  background-color: #9c3d54; /* muted berry red — feminine */
}
.card.neuter {
  --border-main-color: #445a3f;
  background-color: #5b7553; /* muted sage green — neuter */
}
   ```

## Usage

- **Single note**: while editing a note, click the **WW** button in the editor toolbar.
- **Multiple notes**: in the Browser, select the notes, then use
  **Notes ▸ Wordwise: Fetch Frequency, Image & Gender**. A progress window shows
  which note is currently being processed (e.g. "note 12/50 — Rechnung") and can
  be cancelled partway through — already-processed notes keep their changes.

By default, fields that already have content are left untouched — fetching only
fills in blanks. Enable **Overwrite existing Frequency/Image field content** in
Wordwise Settings to always re-fetch and replace instead.

## Notes

- Frequency lookup is fully offline; if a word isn't in your list file, the frequency
  field is left blank.
- Image search requires network access and at least one of the two API keys.
  Pexels is tried first; Pixabay is only used if Pexels finds nothing (missing
  key, no results, or a request error) — the fetch report shows both providers'
  error reasons when neither finds anything. Per both providers' terms, images
  are downloaded and stored in Anki's media folder rather than hotlinked — which
  the add-on already does by design (`images.save_to_media`). Both providers are
  paced to stay under their documented free-tier rate limits: Pexels to 200
  requests/hour (1 every 18s), Pixabay to roughly 1/second. A large bulk fetch
  with many missing images can take a while because of this — the progress
  window shows which note is currently being processed.
- Gender lookup needs no API key. It works for any language freedictionaryapi.com
  covers — including languages with no grammatical gender, which will simply
  never find a gender tag rather than reporting anything misleading.
# wordwise
